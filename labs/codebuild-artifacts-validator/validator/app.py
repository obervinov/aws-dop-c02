"""
This Lambda function validates the contents of CodePipeline artifacts.
"""
import json
import boto3
import hashlib
import logging
import zipfile
import os
import tempfile
import shutil
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def download_and_extract_artifact(s3_client, bucket, key):
    """
    Downloads and extracts a zip artifact. If the artifact contains a nested
    zip file (e.g., 'artifact.zip'), it is also extracted.
    Returns the path to the final extracted contents.
    """
    temp_directory = tempfile.mkdtemp()
    local_zip_path = os.path.join(temp_directory, 'outer_artifact.zip')

    try:
        s3_client.download_file(bucket, key, local_zip_path)
        with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_directory)
            logger.info("Extracted outer zip file contents: %s", os.listdir(temp_directory))

        # Check for nested zip files and extract them
        for filename in os.listdir(temp_directory):
            if filename.endswith('.zip') and filename != 'outer_artifact.zip':
                nested_zip_path = os.path.join(temp_directory, filename)
                logger.info("Found nested zip file: %s. Extracting...", nested_zip_path)
                with zipfile.ZipFile(nested_zip_path, 'r') as nested_zip_ref:
                    nested_zip_ref.extractall(temp_directory)
                    logger.info("Extracted nested zip file contents.")
                # Clean up zip files
                os.remove(nested_zip_path)
                os.remove(local_zip_path)

        final_files_list = os.listdir(temp_directory)
        logger.info("Final extracted files: %s", final_files_list)

        return temp_directory

    except (ClientError, zipfile.BadZipFile) as exception:
        logger.error("Failed to download or extract artifact: %s", exception)
        shutil.rmtree(temp_directory, ignore_errors=True)
        raise


def get_file_hashes(directory):
    """
    Returns a dictionary where the key is the relative file path
    and the value is its hash.
    """
    file_hashes = {}
    for dir_path, _, file_names in os.walk(directory):
        for file_name in sorted(file_names):
            file_path = os.path.join(dir_path, file_name)
            relative_path = os.path.relpath(file_path, directory)

            with open(file_path, 'rb') as file_handle:
                content = file_handle.read()
                file_hashes[relative_path] = hashlib.sha256(content).hexdigest()
    return file_hashes


def lambda_handler(event, context):
    """
    Main function for validating CodePipeline artifacts.
    Compares the hashes of files inside the artifacts.
    """
    temp_directories = []
    try:
        job_id = event['CodePipeline.job']['id']
        input_artifacts = event['CodePipeline.job']['data']['inputArtifacts']

        if not input_artifacts:
            raise ValueError("No input artifacts found in CodePipeline event.")

        uat_artifact_info = input_artifacts[0]
        s3_location = uat_artifact_info['location']['s3Location']

        s3_client = boto3.client('s3')

        # Step 1: Download and extract UAT artifact
        uat_extracted_directory = download_and_extract_artifact(s3_client, s3_location['bucketName'], s3_location['objectKey'])
        temp_directories.append(uat_extracted_directory)

        # Step 2: Download and extract Test artifact
        test_artifact_key = "test-artifact/artifact.zip"
        test_extracted_directory = download_and_extract_artifact(s3_client, s3_location['bucketName'], test_artifact_key)
        temp_directories.append(test_extracted_directory)

        # Step 3: Get dictionaries of file hashes
        uat_file_hashes = get_file_hashes(uat_extracted_directory)
        test_file_hashes = get_file_hashes(test_extracted_directory)
        logger.info("UAT file hashes: %s\n UAT files list: %s", json.dumps(uat_file_hashes, indent=2), json.dumps(os.listdir(uat_extracted_directory), indent=2))
        logger.info("Test file hashes: %s\n Test files list: %s", json.dumps(test_file_hashes, indent=2), json.dumps(os.listdir(test_extracted_directory), indent=2))

        # Step 4: Compare file lists
        if set(uat_file_hashes.keys()) != set(test_file_hashes.keys()):
            mismatched_files = set(uat_file_hashes.keys()) ^ set(test_file_hashes.keys())
            message = f"File lists do not match. Differences: {mismatched_files}"
            logger.error("File lists do not match. Differences: %s", mismatched_files)

            codepipeline_client = boto3.client('codepipeline')
            codepipeline_client.put_job_failure_result(
                jobId=job_id,
                failureDetails={'type': 'JobFailed', 'message': message}
            )
            return

        # Step 5: Compare hashes of each file
        mismatched_hashes = {
            file: (uat_file_hashes[file], test_file_hashes[file])
            for file in uat_file_hashes
            if uat_file_hashes[file] != test_file_hashes[file]
        }

        # Step 6: If there's a difference, log it (just debug info)
        if mismatched_hashes:
            message = f"Validation failed. File hashes do not match: {json.dumps(mismatched_hashes, indent=2)}"
            logger.error("Validation failed. File hashes do not match: %s", json.dumps(mismatched_hashes, indent=2))

            # Log file content
            for file in mismatched_hashes:
                uat_file_path = os.path.join(uat_extracted_directory, file)
                test_file_path = os.path.join(test_extracted_directory, file)
                if os.path.exists(uat_file_path) and os.path.exists(test_file_path):
                    try:
                        with open(uat_file_path, 'r') as uat_file, open(test_file_path, 'r') as test_file:
                            uat_content = uat_file.read()
                            test_content = test_file.read()
                            logger.error("--- Difference in %s ---", file)
                            logger.error("UAT content:\n%s", uat_content)
                            logger.error("Test content:\n%s", test_content)
                    except Exception as content_read_exception:
                        logger.error("Failed to read content of file %s: %s", file, content_read_exception)

            codepipeline_client = boto3.client('codepipeline')
            codepipeline_client.put_job_failure_result(
                jobId=job_id,
                failureDetails={'type': 'JobFailed', 'message': message}
            )
            return

        # Validation is successful
        logger.info("Validation successful. All file hashes match.")
        codepipeline_client = boto3.client('codepipeline')
        codepipeline_client.put_job_success_result(jobId=job_id)
        logger.info("Success signal sent to CodePipeline.")

    except Exception as unexpected_exception:
        logger.error("An unexpected error occurred: %s", unexpected_exception, exc_info=True)
        try:
            codepipeline_client = boto3.client('codepipeline')
            codepipeline_client.put_job_failure_result(
                jobId=event['CodePipeline.job']['id'],
                failureDetails={'type': 'JobFailed', 'message': f'An unexpected error occurred: {unexpected_exception}'}
            )
        except Exception as inner_exception:
            logger.error("Failed to report job failure to CodePipeline: %s", inner_exception, exc_info=True)
    finally:
        for temp_directory in temp_directories:
            if os.path.exists(temp_directory):
                shutil.rmtree(temp_directory, ignore_errors=True)
