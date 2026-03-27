# API Consolidation Context

## Overview
We are consolidating jscom-mini-services from two separate Lambda functions into a single Lambda using AWS Lambda Powertools.

## Current Services Being Consolidated

### 1. My IP Service (GET /v1/ip/my)
- Returns client's public IP from API Gateway request context
- No authentication required
- Current implementation: `lambdas/src/my_ip_lambda.py`

### 2. DNS Update Service (POST /v1/dns/update)
- Updates Route53 A records for dynamic DNS
- Requires authentication via `x-auth-token` header
- Current implementation: `lambdas/src/update_dns_lambda.py`

## New Architecture

### Package Structure
```
lambdas/src/api/
├── __init__.py
├── handler.py          # Main Lambda handler with APIGatewayRestResolver
├── models.py           # Pydantic request/response models
├── middleware.py       # Auth decorator
├── config.py           # Zone mappings config
├── exceptions.py       # Custom API exceptions
└── services/
    ├── __init__.py
    └── dns_service.py  # Route53 operations
```

### Environment Variables
- `AUTH_TOKEN`: Single shared token for protected endpoints
- `ALLOWED_ZONES`: Comma-separated `domain:zone_id` pairs
  - Format: `johnsosoka.com:ZONE1,sosoka.com:ZONE2,sosoka.io:ZONE3,...`
- `DEFAULT_TTL`: Optional, defaults to 300

### Supported Domains
- johnsosoka.com
- sosoka.com
- sosoka.io
- sosoka.org
- section76.net
- j3bin.net
- the-homelab.net

### Request/Response Models

**IpResponse** (GET /v1/ip/my):
```json
{"ip": "x.x.x.x"}
```

**DnsUpdateRequest** (POST /v1/dns/update):
```json
{"domain": "subdomain.example.com.", "ip": "1.2.3.4"}
```
- Domain MUST end with trailing dot
- IP MUST be valid IPv4

**DnsUpdateResponse**:
```json
{
  "message": "DNS record updated successfully",
  "domain": "subdomain.example.com.",
  "ip": "1.2.3.4",
  "change_id": "C1234567890ABC",
  "status": "PENDING"
}
```

**ErrorResponse**:
```json
{"error": "ErrorType", "message": "Human readable message"}
```

### Authentication Pattern
- Protected endpoints use `@require_auth(config)` decorator
- Checks `x-auth-token` header against `AUTH_TOKEN` env var
- Returns 401 if missing, 403 if invalid

### Route53 Logic
- UPSERT action (creates or updates)
- Type: A record
- TTL: From config (default 300)
- Zone ID looked up from domain suffix match

## Key Patterns

### Powertools Usage
```python
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver(enable_validation=True)
logger = Logger(service="jscom-mini-services")
tracer = Tracer(service="jscom-mini-services")
```

### Config Loading
Config loaded at module level for Lambda warm starts:
```python
config = AppConfig.from_env()
```

### API Gateway HTTP API v2 Event
Source IP is at: `event["requestContext"]["http"]["sourceIp"]`
Via Powertools: `app.current_event.request_context.http.source_ip`
