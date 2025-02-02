##############################
# my_ip Lambda & API Gateway Integration
##############################

# Lambda module for my_ip_lambda
module "my_ip_lambda" {
  source             = "terraform-aws-modules/lambda/aws"
  function_name      = var.my_ip_lambda_function_name
  description        = "Returns the requesting client's IP address (similar to whatismyip.com)"
  handler            = "my_ip_lambda.lambda_handler"
  runtime            = "python3.8"
  source_path        = "../lambdas/src/my_ip_lambda.py"
  attach_policy_json = false  # No extra permissions required
  tags = {
    project = local.project_name
  }
}

# API Gateway Integration for my_ip_lambda
resource "aws_apigatewayv2_integration" "my_ip_integration" {
  api_id                 = local.api_gateway_id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = module.my_ip_lambda.lambda_function_invoke_arn
  payload_format_version = "2.0"
}


# API Gateway Route for my_ip_lambda
resource "aws_apigatewayv2_route" "my_ip_route" {
  api_id    = local.api_gateway_id
  route_key = "GET /v1/ip/my"
  target    = "integrations/${aws_apigatewayv2_integration.my_ip_integration.id}"
}

# Lambda Permission to allow API Gateway to invoke my_ip_lambda
resource "aws_lambda_permission" "my_ip_lambda_permission" {
  statement_id  = "AllowMyIPServiceAPIInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.my_ip_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${local.execution_arn}/*/*/*"
}
