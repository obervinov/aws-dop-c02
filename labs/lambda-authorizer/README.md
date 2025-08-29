# SAM Demo HttpApi + Lambda Authorizer

This project contains the source code and supporting files for a serverless application that demonstrates an **Amazon API Gateway HTTP API** with a custom **AWS Lambda Authorizer**. The Lambda Authorizer acts as a mock authentication service, verifying an `Authorization` header before allowing access to a separate Lambda function containing business logic.

The project includes the following files and folders:
- `auth_service/` – Code for the Lambda Authorizer function (mock authentication service).
- `business_logic/` – Code for the main business logic Lambda function.
- `events/` – Invocation event examples that you can use to test functions locally.
- `template.yaml` – The SAM template that defines the application's AWS resources.

The application utilizes several AWS resources, including:
- 2 AWS Lambda functions
- API Gateway HTTP API
- Permission settings for the Lambda function invocations

These resources are defined in the `template.yaml` file. You can update this template to add more AWS resources using the same deployment process.

## Deployment Steps
The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To use the SAM CLI, you need the following tools:
* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)


### Build and Package

You'll need an S3 bucket to store your packaged application artifacts. If you don't have one, create one:
```bash
aws s3 mb s3://lambda-authorizer-demo-packaged
```

Then, build and package your application. The sam build command will compile your code, and sam package will upload the deployment artifacts (ZIP files for your Lambda functions) to the specified S3 bucket.

```bash
sam build --use-container
sam package \
  --template-file template.yaml \
  --output-template-file packaged-template.yaml \
  --s3-bucket lambda-authorizer-demo-packaged
```

### Deploy in AWS

After packaging, deploy your application to AWS using the `packaged-template.yaml`:

```bash
sam deploy \
  --template-file packaged-template.yaml \
  --stack-name sam-lambda-authorizer-demo \
  --capabilities CAPABILITY_IAM \
  --confirm-changeset
```

Alternatively, you can use `sam deploy --guided` for an interactive deployment process that prompts you for details.

During deployment, you'll be prompted for:
- `Stack Name`: A unique name for your CloudFormation stack (e.g., sam-lambda-authorizer-demo).
- `AWS Region`: The AWS region for deployment.
- `Confirm changes before deploy`: Review CloudFormation changes before execution.
- `Allow SAM CLI IAM role creation`: Acknowledge the creation of IAM roles required by your Lambda functions.
- `Save arguments to samconfig.toml`: Save your choices for future deployments.
You can find your API Gateway Endpoint URL in the output values displayed after a successful deployment. Look for the ApiEndpoint output.


### Testing the Deployed API

Once deployed, you can test your API Gateway endpoint using `curl` or Postman. Remember the Authorizer Lambda expects an `Authorization: Bearer <token>` header.

The ApiEndpoint will be displayed in the deployment outputs.
```bash
# Get API Gateway endpoint URL
URL=$(aws cloudformation describe-stacks --stack-name sam-lambda-authorizer-demo --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)
```
- **Access Denied (No token or invalid token):**
```bash
curl -v $URL/Prod/hello
# Expected: HTTP 401 Unauthorized

curl -v -H "Authorization: Bearer wrong-token" $URL/Prod/hello
# Expected: HTTP 403 Forbidden
```

- **Access Denied (by mock authorizer logic):**
```bash
curl -v -H "Authorization: Bearer denied-token" $URL/Prod/hello
# Expected: HTTP 401 Unauthorized or 403 Forbidden (check CloudWatch logs for Authorizer Lambda for details)
```

- **Access Granted (Valid token):**
```bash
curl -v -H "Authorization: Bearer valid-token" $URL/Prod/hello
# Expected: HTTP 200 OK, with a JSON response from your BusinessLogicLambda
# The response body will include details from the Authorizer.
```


## Cleanup
To delete the sample application and all its provisioned AWS resources, use the AWS CLI. Assuming you used `sam-lambda-authorizer-demo` for the stack name, you can run the following:
```bash
sam delete --stack-name sam-lambda-authorizer-demo
aws s3 rb s3://lambda-authorizer-demo-packaged --force
```

## Resources
- [API Gateway HTTP API with Lambda Authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html)
- [Using Lambda Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html)
- [Lambda authorizer examples for AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-controlling-access-to-apis-lambda-authorizer.html)
- [Controlling Access to APIs](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-controlling-access-to-apis.html#serverless-controlling-access-to-apis-choices)
- [Error 500 on Lambda Authorizer](https://repost.aws/questions/QUxIaIVl3CRLWJcKuqcwnD0w/error-500-on-lambda-authorizer)
- [Example: Create a Lambda Authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html#http-api-lambda-authorizer.example-create)