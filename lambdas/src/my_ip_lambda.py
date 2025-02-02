import json


def lambda_handler(event, context):
    """
    AWS Lambda function to return the requesting client's IP address.

    This function serves as a lightweight service similar to whatismyip.com,
    retrieving the client's IP from the API Gateway request context. It is
    designed for invocation via API Gateway with Lambda Proxy Integration.

    Args:
        event (dict): Contains the request details including the client's IP.
        context (LambdaContext): Provides runtime information.

    Returns:
        dict: An HTTP response with a JSON body containing the client's IP address.
    """
    ip_address = event.get("requestContext", {}).get("http", {}).get("sourceIp", "IP not found")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"ip": ip_address})
    }
