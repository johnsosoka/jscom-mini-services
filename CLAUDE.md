# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of lightweight AWS Lambda microservices powering the API for johnsosoka.com. Each service is a standalone Python Lambda function deployed via Terraform and exposed through API Gateway.

## Architecture

- **Lambda Functions**: Python 3.8 handlers in `lambdas/src/`
- **Infrastructure**: Terraform in `terraform/` using terraform-aws-modules/lambda/aws
- **API Gateway**: HTTP API (v2) with Lambda proxy integration, managed in separate jscom-blog repo
- **State Management**: Remote S3 backend with DynamoDB locking

The Terraform configuration pulls shared infrastructure (API Gateway, Route53 hosted zone) from remote state in `jscom-core-infra` and `jscom-blog` projects.

## Current Services

| Service | Endpoint | Handler |
|---------|----------|---------|
| My IP | `GET /v1/ip/my` | `my_ip_lambda.lambda_handler` |
| DNS Update | `POST /v1/dns/update` | `update_dns_lambda.lambda_handler` |

## Commands

### Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

The `auth_token` variable is sensitive and must be provided at runtime (e.g., via `TF_VAR_auth_token` or `-var`).

### Python Dependencies

```bash
pip install -r lambdas/requirements.txt
```

## Adding a New Lambda Service

1. Create handler in `lambdas/src/<service_name>_lambda.py`
2. Create Terraform file `terraform/<service_name>_lambda.tf` following existing patterns:
   - Lambda module definition
   - API Gateway integration
   - API Gateway route
   - Lambda permission for API Gateway invocation
3. Add any required variables to `terraform/variables.tf`
