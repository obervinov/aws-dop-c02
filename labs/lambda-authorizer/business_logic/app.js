exports.handler = async (event) => {
    console.log('Business Logic Lambda received event:', JSON.stringify(event, null, 2));

    // Access the authorization context passed by the Authorizer
    // event.requestContext.authorizer.lambda is the path for HTTP API Authorizer v2
    const userId = event.requestContext.authorizer && event.requestContext.authorizer.lambda && event.requestContext.authorizer.lambda.userId;
    const roles = event.requestContext.authorizer && event.requestContext.authorizer.lambda && event.requestContext.authorizer.lambda.roles;
    const customData = event.requestContext.authorizer && event.requestContext.authorizer.lambda && event.requestContext.authorizer.lambda.customData;
    const messageFromAuthorizer = event.requestContext.authorizer && event.requestContext.authorizer.lambda && event.requestContext.authorizer.lambda.message;


    let greetingMessage = `Hello from Business Logic!`;
    if (userId) {
        greetingMessage += ` Authenticated as User: ${userId} with Roles: ${roles}.`;
    }
    if (customData) {
        greetingMessage += ` Custom data from Authorizer: "${customData}".`;
    } else if (messageFromAuthorizer) {
        greetingMessage += ` Message from Authorizer: "${messageFromAuthorizer}".`;
    }


    const response = {
        statusCode: 200,
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: greetingMessage }),
    };
    return response;
};