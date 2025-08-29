# SAM Lambda Authorizer Demo

This project contains the source code and supporting files for a serverless application that demonstrates an **Amazon API Gateway HTTP API** with a custom **AWS Lambda Authorizer**. The Lambda Authorizer acts as a mock authentication service, verifying an `Authorization` header before allowing access to a separate Lambda function containing business logic.

The project includes the following files and folders:
`auth_service/` – Code for the Lambda Authorizer function (our mock authentication service).
`business_logic/` – Code for the main business logic Lambda function.
`events/` – Invocation event examples that you can use to test functions locally.
`template.yaml` – The SAM template that defines the application's AWS resources.

The application utilizes several AWS resources, including two AWS Lambda functions and an API Gateway HTTP API. These resources are defined in the `template.yaml` file. You can update this template to add more AWS resources using the same deployment process.

If you prefer to use an integrated development environment (IDE) to build and test your application, consider using the AWS Toolkit. The AWS Toolkit is an open-source plug-in for popular IDEs that leverages the SAM CLI to build and deploy serverless applications on AWS. It also provides a simplified step-through debugging experience for Lambda function code. You can find more information here:

* [CLion](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [GoLand](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [IntelliJ](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [WebStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [Rider](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [PhpStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [PyCharm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [RubyMine](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [DataGrip](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [VS Code](https://docs.aws.amazon.com/toolkit-for-vscode/latest/userguide/welcome.html)
* [Visual Studio](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/welcome.html)

## Deployment Steps
The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To use the SAM CLI, you need the following tools:
* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)


1. Build and Package

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

2. Deploy in AWS

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


3. Testing the Deployed API

Once deployed, you can test your API Gateway endpoint using `curl` or Postman. Remember the Authorizer Lambda expects an `Authorization: Bearer <token>` header.

The ApiEndpoint will be displayed in the deployment outputs.

- **Access Denied (No token or invalid token):**
```bash
# Get API Gateway endpoint URL
URL=$(aws cloudformation describe-stacks --stack-name sam-lambda-authorizer-demo --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)

curl -v $URL/Prod/hello
# Expected: HTTP 401 Unauthorized or 403 Forbidden

curl -v -H "Authorization: Bearer wrong-token" $URL/Prod/hello
# Expected: HTTP 401 Unauthorized or 403 Forbidden
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
# The response body will include details like userId and roles passed from the Authorizer.
```


## Local Development and Testing
Build your application with the `sam build --use-container` command:
```bash
sam build --use-container
```
The SAM CLI installs dependencies (if defined in `package.json` or `requirements.txt` within your function directories), creates a deployment package, and saves it in the `.aws-sam/build` folder.

**Invoke Functions Locally**

You can test individual functions by invoking them directly with a test event. Test events can be created in the `events/` folder of this project.

For example, to test your authorizer function locally, you'd create an event file (`events/authorizer-event.json`) that mimics the event object API Gateway sends to an authorizer.
```bash
sam local invoke AuthServiceLambda --event events/authorizer-event.json
```

To test your business logic function locally:
```bash
sam local invoke BusinessLogicLambda --event events/business-logic-event.json
```

**Run the API Locally**

The SAM CLI can also emulate your application's API Gateway locally. Use sam local start-api to run the API on port 3000 (by default):
```bash
sam local start-api
```

Then, you can send requests to `http://localhost:3000/hello` with the appropriate `Authorization` header to test the full flow locally.
```bash
# Test locally with a valid token
curl -v -H "Authorization: Bearer valid-token" http://localhost:3000/hello

# Test locally without a token
curl -v http://localhost:3000/hello
```
The `SAM CLI` reads your template.yaml to determine the API's routes and the functions they invoke, including the custom authorizer configuration.


## Fetching Lambda Function Logs
To simplify troubleshooting, SAM CLI provides the `sam logs` command. This command fetches logs generated by your deployed Lambda functions from CloudWatch Logs.
```bash
# Fetch logs for the Authorizer Lambda
sam logs -n AuthServiceLambda --stack-name "sam-lambda-authorizer-demo" --tail

# Fetch logs for the Business Logic Lambda
sam logs -n BusinessLogicLambda --stack-name "sam-lambda-authorizer-demo" --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).


## Add a Resource to Your Application
The application template uses AWS Serverless Application Model (AWS SAM) to define application resources. AWS SAM is an extension of AWS CloudFormation with a simpler syntax for configuring common serverless application resources such as functions, triggers, and APIs. For resources not included in [the SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), you can use standard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) resource types.


## Cleanup
To delete the sample application and all its provisioned AWS resources, use the AWS CLI. Assuming you used `sam-lambda-authorizer-demo` for the stack name, you can run the following:
```bash
sam delete --stack-name sam-lambda-authorizer-demo
```

## Resources
- [API Gateway HTTP API with Lambda Authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html)
- [Using Lambda Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html)
- [Lambda authorizer examples for AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-controlling-access-to-apis-lambda-authorizer.html)
- [Controlling Access to APIs](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-controlling-access-to-apis.html#serverless-controlling-access-to-apis-choices)