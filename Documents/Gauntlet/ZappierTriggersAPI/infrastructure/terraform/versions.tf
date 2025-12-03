# Terraform and Provider Versions

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Backend configuration - override per environment
  # backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "zapier-triggers-api"
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "ZappierTriggersAPI"
    }
  }
}
