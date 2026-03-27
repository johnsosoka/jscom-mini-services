##############################
# Consolidated API Lambda & API Gateway Integration
##############################

locals {
  # Format allowed_zones map into comma-separated domain:zone_id string
  allowed_zones_str = join(",", [
    for domain, zone_id in var.allowed_zones : "${domain}:${zone_id}"
  ])

  # Build list of zone ARNs for IAM policy
  zone_arns = [
    for zone_id in values(var.allowed_zones) : "arn:aws:route53:::hostedzone/${zone_id}"
  ]
}

# Lambda module for consolidated API
module "api_lambda" {
  source        = "terraform-aws-modules/lambda/aws"
  function_name = var.api_lambda_function_name
  description   = "Consolidated API Lambda for jscom-mini-services (IP lookup, DNS updates)"
  handler       = "api.handler.lambda_handler"
  runtime       = "python3.13"

  source_path = "../lambdas/src"

  # Use AWS managed Powertools layer (includes Pydantic)
  layers = [
    "arn:aws:lambda:us-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-x86_64:7"
  ]

  # Enable X-Ray tracing
  tracing_mode = "Active"

  environment_variables = {
    AUTH_TOKEN              = var.auth_token
    ALLOWED_ZONES           = local.allowed_zones_str
    DEFAULT_TTL             = tostring(var.default_ttl)
    POWERTOOLS_SERVICE_NAME = "jscom-mini-services"
    POWERTOOLS_LOG_LEVEL    = "INFO"
  }

  # Only attach Route53 policy if allowed_zones is not empty
  attach_policy_json = length(var.allowed_zones) > 0
  policy_json = length(var.allowed_zones) > 0 ? jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["route53:ChangeResourceRecordSets"]
        Resource = local.zone_arns
      }
    ]
  }) : null

  memory_size = 256
  timeout     = 30

  tags = {
    project = local.project_name
  }
}

# API Gateway Integration for consolidated API Lambda
resource "aws_apigatewayv2_integration" "api_integration" {
  api_id                 = local.api_gateway_id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = module.api_lambda.lambda_function_invoke_arn
  payload_format_version = "2.0"
}

# API Gateway Route for My IP endpoint
resource "aws_apigatewayv2_route" "my_ip_route" {
  api_id    = local.api_gateway_id
  route_key = "GET /v1/ip/my"
  target    = "integrations/${aws_apigatewayv2_integration.api_integration.id}"
}

# API Gateway Route for DNS Update endpoint
resource "aws_apigatewayv2_route" "dns_update_route" {
  api_id    = local.api_gateway_id
  route_key = "POST /v1/dns/update"
  target    = "integrations/${aws_apigatewayv2_integration.api_integration.id}"
}

# Lambda Permission to allow API Gateway to invoke consolidated API Lambda
resource "aws_lambda_permission" "api_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.api_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${local.execution_arn}/*/*/*"
}

##############################
# API Gateway Rate Limiting
##############################

# Configure per-route throttling on the API Gateway stage
# Note: The stage is created by jscom-blog but we manage route-level throttling here
resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = local.api_gateway_id
  name        = "$default"
  auto_deploy = true

  # Per-route throttling settings
  route_settings {
    route_key              = aws_apigatewayv2_route.my_ip_route.route_key
    throttling_rate_limit  = var.ip_endpoint_rate_limit
    throttling_burst_limit = var.ip_endpoint_burst_limit
  }

  route_settings {
    route_key              = aws_apigatewayv2_route.dns_update_route.route_key
    throttling_rate_limit  = var.dns_endpoint_rate_limit
    throttling_burst_limit = var.dns_endpoint_burst_limit
  }

  # Preserve settings managed by jscom-blog project
  lifecycle {
    ignore_changes = [
      access_log_settings,
      deployment_id,
      tags,
    ]
  }
}
