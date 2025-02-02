##############################
# update_dns Lambda integration
##############################

module "update_dns_lambda" {
  source             = "terraform-aws-modules/lambda/aws"
  function_name      = var.update_dns_lambda_function_name
  description        = "Updates a DNS record in Route53 for dynamic services (e.g., Minecraft server)"
  handler            = "update_dns_lambda.lambda_handler"
  runtime            = "python3.8"
  source_path        = "../lambdas/src/update_dns_lambda.py"
  attach_policy_json = true
  policy_json        = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "route53:ChangeResourceRecordSets"
        ]
        Resource = "arn:aws:route53:::hostedzone/${local.root_zone_id}"
      }
    ]
  })

  environment_variables = {
    AUTH_TOKEN     = var.auth_token
    HOSTED_ZONE_ID = local.root_zone_id
  }

  tags = {
    project = local.project_name
  }
}

resource "aws_apigatewayv2_integration" "update_dns_integration" {
  api_id                 = local.api_gateway_id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"   # Must be POST for Lambda proxy integrations
  integration_uri        = module.update_dns_lambda.lambda_function_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "update_dns_route" {
  api_id    = local.api_gateway_id
  route_key = "POST /v1/dns/update"
  target    = "integrations/${aws_apigatewayv2_integration.update_dns_integration.id}"
}

resource "aws_lambda_permission" "update_dns_lambda_permission" {
  statement_id  = "AllowUpdateDNSAPIInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.update_dns_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${local.execution_arn}/*/*/*"
}
