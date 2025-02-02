provider "aws" {
  region = "us-west-2"
}

// Terraform state managed remotely.
terraform {
  backend "s3" {
    bucket         = "jscom-tf-backend"
    key            = "project/jscom-mini-services/state/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "terraform-state"
  }
}

data "terraform_remote_state" "jscom_common_data" {
  backend = "s3"
  config = {
    bucket  = "jscom-tf-backend"
    key     = "project/jscom-core-infra/state/terraform.tfstate"
    region  = "us-west-2"
  }
}

data "terraform_remote_state" "jscom_web_data" {
  backend = "s3"
  config = {
    bucket  = "jscom-tf-backend"
    key     = "project/jscom-blog/state/terraform.tfstate"
    region  = "us-west-2"
  }
}

locals {
  project_name = "jscom-mini-services"
  execution_arn = data.terraform_remote_state.jscom_web_data.outputs.api_gateway_execution_arn
  api_domain_name = data.terraform_remote_state.jscom_web_data.outputs.custom_domain_name
  api_gateway_id = data.terraform_remote_state.jscom_web_data.outputs.api_gateway_id
  api_gateway_target = data.terraform_remote_state.jscom_web_data.outputs.custom_domain_name_target
}