import os
import json
import boto3

def lambda_handler(event, context):
    """
    Update a DNS A record in Route53.

    This function supports dynamic DNS updates (for example, updating a Minecraft server's external IP).
    It expects a JSON payload with:
      - domain: the DNS record name (e.g. "minecraft.example.com.")
      - ip: the new A record value (e.g. "1.2.3.4")

    The authorization token is expected in the request headers (key "x-auth-token"). The token is verified against
    the AUTH_TOKEN environment variable.

    Returns:
        dict: HTTP response containing a status message.
    """
    expected_token = os.environ.get("AUTH_TOKEN")
    hosted_zone_id = os.environ.get("HOSTED_ZONE_ID")

    # Retrieve auth token from headers
    headers = event.get("headers", {})
    auth_token = headers.get("x-auth-token")

    if auth_token != expected_token:
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Unauthorized"})
        }

    body = event.get("body")
    if body:
        try:
            data = json.loads(body)
        except Exception:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid JSON payload"})
            }
    else:
        data = {}

    domain = data.get("domain")
    new_ip = data.get("ip")
    if not domain or not new_ip:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing 'domain' or 'ip' parameter"})
        }

    if not hosted_zone_id:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Hosted zone ID not configured"})
        }

    route53 = boto3.client("route53")
    try:
        response = route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Comment": "Auto-updated by update_dns_lambda",
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": domain,
                            "Type": "A",
                            "TTL": 300,
                            "ResourceRecords": [{"Value": new_ip}]
                        }
                    }
                ]
            }
        )
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to update DNS record",
                "message": str(e)
            }, default=str)
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "DNS record updated",
            "change_info": response
        }, default=str)
    }
