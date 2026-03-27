# jscom-mini-services

A collection of lightweight AWS Lambda microservices powering the API for johnsosoka.com. Built with a consolidated single-Lambda architecture using AWS Powertools for Python, providing routing, observability, and validation.

## Architecture

The service uses a modern serverless architecture with the following components:

- **Single Lambda Function**: Consolidated handler using AWS Powertools `APIGatewayHttpResolver` for HTTP routing
- **Runtime**: Python 3.13
- **API Gateway**: HTTP API (v2) with Lambda proxy integration
- **Infrastructure**: Terraform with remote state management (S3 backend, DynamoDB locking)
- **Observability**: AWS X-Ray tracing enabled via Powertools
- **Multi-Domain DNS Support**: Route53 integration for multiple domains

### Supported Domains

The DNS update service supports the following domains:

- johnsosoka.com
- sosoka.com
- sosoka.io
- sosoka.org
- section76.net
- j3bin.net
- the-homelab.net

## API Endpoints

### GET /v1/ip/my

Returns the client's public IP address.

**Response:**

```json
{
  "ip": "203.0.113.42"
}
```

**Example:**

```bash
curl https://api.johnsosoka.com/v1/ip/my
```

### POST /v1/dns/update

Updates a Route53 DNS A record. Protected endpoint requiring authentication.

**Headers:**

- `x-auth-token`: Authentication token (required)
- `Content-Type`: application/json

**Request Body:**

```json
{
  "domain": "subdomain.example.com.",
  "ip": "203.0.113.42"
}
```

**Requirements:**

- Domain must include trailing dot (DNS FQDN format)
- IP must be valid IPv4 address
- Domain must match one of the allowed zones

**Response:**

```json
{
  "message": "DNS record updated successfully",
  "domain": "subdomain.example.com.",
  "ip": "203.0.113.42",
  "change_id": "C1234567890ABC",
  "status": "PENDING"
}
```

**Example:**

```bash
curl -X POST https://api.johnsosoka.com/v1/dns/update \
  -H "Content-Type: application/json" \
  -H "x-auth-token: your-token-here" \
  -d '{
    "domain": "mc.johnsosoka.com.",
    "ip": "203.0.113.42"
  }'
```

## Directory Structure

```
jscom-mini-services/
├── lambdas/
│   ├── src/api/              # Lambda package
│   │   ├── handler.py        # Main handler with routes
│   │   ├── config.py         # Zone configuration
│   │   ├── models.py         # Pydantic request/response models
│   │   ├── middleware.py     # Authentication decorator
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── services/         # Business logic
│   │       └── dns.py        # Route53 DNS service
│   ├── tests/                # Unit tests (63 tests)
│   ├── pyproject.toml        # Poetry configuration
│   └── requirements.txt      # Lambda layer dependencies
├── terraform/                # Infrastructure as code
│   ├── main.tf              # Primary Lambda configuration
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Output values
│   └── terraform.tfvars     # Environment-specific values
├── jscom-api-client/        # Python client library
└── README.md
```

## Python Client Library

A Python client library and CLI tool are available in the `jscom-api-client/` subdirectory.

### Installation

Install from GitHub:

```bash
pip install "git+https://github.com/johnsosoka/jscom-mini-services.git#subdirectory=jscom-api-client"
```

Using Poetry:

```bash
poetry add "git+https://github.com/johnsosoka/jscom-mini-services.git#subdirectory=jscom-api-client"
```

### Library Usage

```python
from jscom_api import JscomApiClient

# Get public IP
with JscomApiClient() as client:
    response = client.get_my_ip()
    print(response.ip)

# Update DNS record
client = JscomApiClient(auth_token="your-token-here")
try:
    response = client.update_dns("subdomain.example.com.", "203.0.113.42")
    print(f"Status: {response.status}")
    print(f"Change ID: {response.change_id}")
finally:
    client.close()
```

### CLI Usage

```bash
# Get your public IP
jscom-api ip

# Update DNS record with specific IP
jscom-api dns update --domain mc.example.com. --ip 203.0.113.42

# Update DNS record with current public IP
jscom-api dns update --domain mc.example.com. --use-current-ip
```

See `jscom-api-client/README.md` for complete documentation.

## Terraform Deployment

### Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- AWS profile: `jscom` (or modify provider configuration)

### Required Environment Variables

Configure these variables in `terraform/terraform.tfvars` or via environment variables:

- `AUTH_TOKEN`: Authentication token for protected endpoints
- `ALLOWED_ZONES`: Comma-separated domain:zone_id pairs

Example `ALLOWED_ZONES` format:

```
johnsosoka.com:Z1234567890ABC,sosoka.com:Z0987654321XYZ
```

### Optional Variables

- `DEFAULT_TTL`: DNS record TTL in seconds (default: 300)

### Deployment

```bash
cd terraform

# Initialize Terraform (first time only)
terraform init

# Review planned changes
terraform plan -var="auth_token=$AUTH_TOKEN" -var-file="terraform.tfvars"

# Apply infrastructure changes
terraform apply -var="auth_token=$AUTH_TOKEN" -var-file="terraform.tfvars"
```

The deployment creates:

- Lambda function with Python 3.13 runtime
- IAM role with Route53 permissions for allowed zones
- API Gateway HTTP API integration
- CloudWatch log group for Lambda logs
- X-Ray tracing configuration

## Development

### Setup

```bash
cd lambdas
poetry install
```

### Run Tests

```bash
poetry run pytest -v
```

### Code Quality

```bash
# Type checking
poetry run mypy src/

# Linting
poetry run ruff check src/

# Format code
poetry run ruff format src/
```

### Project Dependencies

Key dependencies:

- `aws-lambda-powertools[aws-sdk]`: Routing, logging, tracing, validation
- `pydantic`: Request/response validation
- `boto3`: AWS SDK for Route53 operations

## Adding New Endpoints

1. Define Pydantic models in `lambdas/src/api/models.py`
2. Add route handler in `lambdas/src/api/handler.py` using `@app.get()` or `@app.post()`
3. Implement business logic in `lambdas/src/api/services/`
4. Add unit tests in `lambdas/tests/`
5. Deploy via Terraform

Example:

```python
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver

app = APIGatewayHttpResolver(enable_validation=True)

@app.get("/v1/example")
def get_example() -> ExampleResponse:
    return ExampleResponse(data="example")
```

## License

This project is licensed under the terms of the LICENSE file.

## Contributing

This is a personal project, but contributions are welcome. Feel free to open issues or submit pull requests.
