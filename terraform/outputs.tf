##############################
# Consolidated API Lambda Outputs
##############################

output "api_lambda_function_arn" {
  description = "ARN of the consolidated API Lambda function"
  value       = module.api_lambda.lambda_function_arn
}

output "api_lambda_function_name" {
  description = "Name of the consolidated API Lambda function"
  value       = module.api_lambda.lambda_function_name
}
