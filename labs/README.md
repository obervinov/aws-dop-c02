# Labs
All experiments describes as **CloudFormation** templates or **SAM** projects because they provide a declarative way to manage AWS resources - easy to create, easy to clean up and avoid redundant charges.</br>
Also:
- repeatable
- versioned
- easy to update


## Experiments
1. **Web application errors monitoring**
   - **Description:** This experiment demonstrates how to monitor errors in a web application using AWS services and receive notifications.
   - **Template:** `application-errors-monitoring/deploy.yaml`</br>
        Create ELB, EC2 instances with ELB, CloudWatch Logs and SNS topic.</br>
        First - prepare the environment (some CloudFormation parameters use SSM)</br>
        - add your ssh key pair (if not already added)
            ```bash
            aws ec2 import-key-pair --key-name <your-key-name> --public-key-material file://~/.ssh/id_rsa.pub
            ```
        - add key pair name into the Parameter Store
            ```bash
            aws ssm put-parameter --name ssh-key-name --type String --value <your-key-name>
            ```
        - add email address into the Parameter Store
            ```bash
            aws ssm put-parameter --name sns-email-notification-address --type String --value <your-email-address>
            ```
        ```bash
        # Set up the web application monitoring environment
        aws cloudformation create-stack --stack-name app-errors-monitoring --template-body file://application-errors-monitoring/deploy.yaml --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

        # DON'T FORGET TO CONFIRM SNS EMAIL SUBSCRIPTION (check your email)

        # Get web application URL
        URL=$(aws cloudformation describe-stacks --stack-name app-errors-monitoring --query "Stacks[0].Outputs[?OutputKey=='WebAppUrl'].OutputValue" --output text)

        # Check web application health
        curl $URL

        # Generate bad client codes
        for i in {1..5}; do curl -f $URL/does-not-exist-path; done
        ```

2. **CodeBuild and Lambda Integration**
   - Description: This experiment demonstrates how to integrate AWS CodeBuild with AWS Lambda using a CodePipeline.
   - Templates:
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
