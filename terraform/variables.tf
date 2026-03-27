#
# Consolidated API Lambda
#

variable "api_lambda_function_name" {
  description = "Lambda function name for the consolidated API service."
  type        = string
  default     = "jscom-api-lambda"
}

variable "allowed_zones" {
  description = "Map of domain to Route53 hosted zone ID for DNS updates. Example: {\"johnsosoka.com\" = \"Z1234567890ABC\"}"
  type        = map(string)
}

variable "default_ttl" {
  description = "Default TTL for DNS records in seconds."
  type        = number
  default     = 300
}

variable "auth_token" {
  description = "Authorization token for protected API endpoints."
  type        = string
  sensitive   = true
}

#
# Rate Limiting
#

variable "ip_endpoint_rate_limit" {
  description = "Rate limit (requests per second) for GET /v1/ip/my endpoint."
  type        = number
  default     = 10
}

variable "ip_endpoint_burst_limit" {
  description = "Burst limit for GET /v1/ip/my endpoint."
  type        = number
  default     = 20
}

variable "dns_endpoint_rate_limit" {
  description = "Rate limit (requests per second) for POST /v1/dns/update endpoint."
  type        = number
  default     = 1
}

variable "dns_endpoint_burst_limit" {
  description = "Burst limit for POST /v1/dns/update endpoint."
  type        = number
  default     = 5
}

#
# DEPRECATED: Legacy Lambda variables (remove after migration)
#

# DEPRECATED: Use api_lambda_function_name instead
variable "my_ip_lambda_function_name" {
  description = "DEPRECATED: Lambda function name for the my_ip service. Use api_lambda_function_name instead."
  type        = string
  default     = "my_ip_lambda"
}

# DEPRECATED: Use api_lambda_function_name instead
variable "update_dns_lambda_function_name" {
  description = "DEPRECATED: Lambda function name for the DNS update service. Use api_lambda_function_name instead."
  type        = string
  default     = "update_dns_lambda"
}