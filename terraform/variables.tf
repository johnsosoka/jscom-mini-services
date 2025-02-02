#
# What is My IP Lambda
#

variable "my_ip_lambda_function_name" {
  description = "Lambda function name for the my_ip service."
  type        = string
  default     = "my_ip_lambda"
}

#
# Update DNS Lambda
#

variable "update_dns_lambda_function_name" {
  description = "Lambda function name for the DNS update service."
  type        = string
  default     = "update_dns_lambda"
}

variable "auth_token" {
  description = "Authorization token for updating DNS records."
  type        = string
  sensitive   = true
}