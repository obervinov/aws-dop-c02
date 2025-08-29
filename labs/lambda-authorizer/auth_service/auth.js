// auth_service/auth.js
// https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
exports.handler = async (event) => {
    console.log('Authorizer Lambda received event:', JSON.stringify(event, null, 2));

    const token = event.headers.authorization; // Get Authorization header

    let isAuthorized = false;
    let context = {};

    // Example: if token is "Bearer valid-token", allow access
    if (token && token === 'Bearer valid-token') {
        isAuthorized = true;
        context = { // Authorization context available to target Lambda
            'message': 'authorized with valid-token'
        };
        console.log('Authorization successful for principal: user123');
    } else if (token && token === 'Bearer denied-token') {
        isAuthorized = false;
        context = {
            'message': 'Access denied by mock authorizer.'
        };
        console.log('Authorization denied for principal: user456');
    } else {
        // If token is missing or invalid, deny access
        isAuthorized = false;
        context = {
            'message': 'No valid token provided.'
        };
        console.log('Authorization failed: No valid token provided.');
    }

    // Return simplified response expected with EnableSimpleResponses: true
    const response = {
        isAuthorized: isAuthorized,
        context: context
    };
    console.log('Authorizer Lambda returning response:', JSON.stringify(response, null, 2));

    return response;
};
