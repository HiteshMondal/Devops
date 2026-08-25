########################################
# platform/infra/terraform/provider.tf
# Provider configuration only. See main.tf for the terraform{}/backend
# block and shared data sources/locals.
########################################

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}
