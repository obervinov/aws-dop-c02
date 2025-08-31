"""This is a sample Lambda function from AWS Quick Template from SAM"""

import json
import os

RELEASE_VERSION = 'v1.0'


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    strategy = os.environ.get('DEPLOYMENT_STRATEGY', None)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Hello world. Lambda {RELEASE_VERSION} ({strategy})"
        }),
    }
