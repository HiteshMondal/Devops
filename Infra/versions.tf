# versions.tf - Terraform and provider versions
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  # Backend configuration for state management
  backend "s3" {
    bucket         = "bucket-440597412995"
    key            = "infrastructure/terraform.tfstate"
    region         = "eu-north-1"
    encrypt        = true
    use_lockfile   = true
  }
}

# Provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "DevOps-Demo"
      ManagedBy   = "Terraform"
      Owner       = var.owner_email
    }
  }
}