**CodeBuild and Lambda Integration**
   - **Description:** This experiment demonstrates how to integrate AWS CodeBuild with AWS Lambda using a CodePipeline.
   - **Templates:**
        - `codepipeline-experiments/0.codedeploy-env.yaml` (Create the general dependencies of this experiment)
            ```bash
            # Deploy the general environment
            aws cloudformation create-stack --stack-name codedeploy-environment --template-body file://codepipeline-experiments/0.codedeploy-env.yaml
            ```
        - `codepipeline-experiments/1.codebuild-lambda.yaml` (Create the specific resources to build and deploy the Lambda function)
            ```bash
            # Deploy the CodeBuild and Lambda resources
            aws cloudformation create-stack --stack-name codedeploy-lambda --template-body file://codepipeline-experiments/1.codebuild-lambda.yaml --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
            ```
        - `codepipeline-experiments/2.pipeline-lambda-invocation.yaml` (Create the CodePipeline for the Lambda function invocation)
        - `codepipeline-experiments/3.pipeline-parallel-jobs.yaml` (Create the CodePipeline with parallel jobs)

    Cleanup environment
    ```bash
    aws cloudformation delete-stack --stack-name codedeploy-lambda
    aws cloudformation delete-stack --stack-name codedeploy-environment
    ```