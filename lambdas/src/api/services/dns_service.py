"""Route53 DNS record management service."""

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

from ..config import AppConfig
from ..models import DnsUpdateRequest, DnsUpdateResponse
from ..exceptions import DomainNotAllowedError, DnsUpdateError

logger = Logger(service="jscom-mini-services", child=True)


class DnsService:
    """Service for managing Route53 DNS records."""

    def __init__(self, config: AppConfig):
        """
        Initialize DNS service.

        Args:
            config: Application configuration with zone mappings
        """
        self.config = config
        self.route53_client = boto3.client("route53")

    def update_record(self, request: DnsUpdateRequest) -> DnsUpdateResponse:
        """
        Update or create a DNS A record in Route53.

        Args:
            request: DNS update request with domain and IP

        Returns:
            DnsUpdateResponse with change details

        Raises:
            DomainNotAllowedError: If domain is not in allowed zones
            DnsUpdateError: If Route53 API call fails
        """
        # Find the appropriate hosted zone for this domain
        zone_config = self.config.get_zone_for_domain(request.domain)
        if not zone_config:
            logger.warning(
                "Domain not allowed",
                extra={"domain": request.domain},
            )
            raise DomainNotAllowedError(request.domain)

        logger.info(
            "Updating DNS record",
            extra={
                "domain": request.domain,
                "ip": request.ip,
                "zone_id": zone_config.zone_id,
                "ttl": self.config.default_ttl,
            },
        )

        try:
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_config.zone_id,
                ChangeBatch={
                    "Comment": "Auto-updated by jscom-mini-services consolidated Lambda",
                    "Changes": [
                        {
                            "Action": "UPSERT",
                            "ResourceRecordSet": {
                                "Name": request.domain,
                                "Type": "A",
                                "TTL": self.config.default_ttl,
                                "ResourceRecords": [{"Value": request.ip}],
                            },
                        }
                    ],
                },
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(
                "Route53 API error",
                extra={
                    "error_code": error_code,
                    "error_message": error_message,
                    "domain": request.domain,
                },
            )
            raise DnsUpdateError(f"Failed to update DNS record: {error_message}")
        except Exception as e:
            logger.error(
                "Unexpected error updating DNS",
                extra={"error": str(e), "domain": request.domain},
            )
            raise DnsUpdateError(f"Unexpected error updating DNS record: {str(e)}")

        # Extract change info from response
        change_info = response.get("ChangeInfo", {})
        change_id = change_info.get("Id", "").split("/")[-1]  # Extract ID from ARN
        status = change_info.get("Status", "UNKNOWN")

        logger.info(
            "DNS record updated successfully",
            extra={
                "domain": request.domain,
                "change_id": change_id,
                "status": status,
            },
        )

        return DnsUpdateResponse(
            message="DNS record updated successfully",
            domain=request.domain,
            ip=request.ip,
            change_id=change_id,
            status=status,
        )
