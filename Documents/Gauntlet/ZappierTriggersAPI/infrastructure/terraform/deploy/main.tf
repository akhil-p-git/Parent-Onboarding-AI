# Multi-App Deployment
# Deploy shared infrastructure + all apps

terraform {
  required_version = ">= 1.0.0"

  # Uncomment to use S3 backend
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "multi-app/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  # }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "multi-app-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# Local variables
# -----------------------------------------------------------------------------
locals {
  # Define your 5 apps here
  apps = {
    "triggers-api" = {
      container_image   = "${module.shared.ecr_repository_urls["triggers-api"]}:latest"
      container_port    = 8000
      cpu               = 256
      memory            = 512
      desired_count     = 1
      health_check_path = "/api/v1/health"
      listener_priority = 100
      host_headers      = ["triggers.${var.domain}"]
      path_patterns     = null
      enable_queue      = true
      env_vars          = []
    }

    "app2" = {
      container_image   = "${module.shared.ecr_repository_urls["app2"]}:latest"
      container_port    = 8000
      cpu               = 256
      memory            = 512
      desired_count     = 1
      health_check_path = "/health"
      listener_priority = 200
      host_headers      = ["app2.${var.domain}"]
      path_patterns     = null
      enable_queue      = false
      env_vars          = []
    }

    "app3" = {
      container_image   = "${module.shared.ecr_repository_urls["app3"]}:latest"
      container_port    = 3000
      cpu               = 256
      memory            = 512
      desired_count     = 1
      health_check_path = "/health"
      listener_priority = 300
      host_headers      = ["app3.${var.domain}"]
      path_patterns     = null
      enable_queue      = false
      env_vars          = []
    }

    "app4" = {
      container_image   = "${module.shared.ecr_repository_urls["app4"]}:latest"
      container_port    = 8080
      cpu               = 256
      memory            = 512
      desired_count     = 1
      health_check_path = "/healthz"
      listener_priority = 400
      host_headers      = ["app4.${var.domain}"]
      path_patterns     = null
      enable_queue      = true
      env_vars          = []
    }

    "app5" = {
      container_image   = "${module.shared.ecr_repository_urls["app5"]}:latest"
      container_port    = 8000
      cpu               = 256
      memory            = 512
      desired_count     = 1
      health_check_path = "/health"
      listener_priority = 500
      host_headers      = ["app5.${var.domain}"]
      path_patterns     = null
      enable_queue      = false
      env_vars          = []
    }
  }
}

# -----------------------------------------------------------------------------
# Shared Infrastructure
# -----------------------------------------------------------------------------
module "shared" {
  source = "../shared"

  aws_region  = var.aws_region
  environment = var.environment
  app_names   = keys(local.apps)

  # VPC
  vpc_cidr              = "10.0.0.0/16"
  availability_zones    = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnet_cidrs   = ["10.0.101.0/24", "10.0.102.0/24"]
  database_subnet_cidrs = ["10.0.201.0/24", "10.0.202.0/24"]

  # RDS - shared across all apps
  rds_instance_class        = var.rds_instance_class
  rds_allocated_storage     = 20
  rds_max_allocated_storage = 100

  # Redis - shared across all apps
  redis_node_type = var.redis_node_type

  # SSL Certificate (optional)
  certificate_arn = var.certificate_arn
}

# -----------------------------------------------------------------------------
# Deploy Each App
# -----------------------------------------------------------------------------
module "apps" {
  source   = "../modules/app"
  for_each = local.apps

  aws_region  = var.aws_region
  environment = var.environment
  app_name    = each.key

  # Container config
  container_image   = each.value.container_image
  container_port    = each.value.container_port
  cpu               = each.value.cpu
  memory            = each.value.memory
  desired_count     = each.value.desired_count
  health_check_path = each.value.health_check_path

  # Routing
  listener_priority = each.value.listener_priority
  host_headers      = each.value.host_headers
  path_patterns     = each.value.path_patterns

  # Queue
  enable_queue = each.value.enable_queue

  # Environment - each app gets its own database
  database_url = "postgresql://postgres:PASSWORD@${module.shared.database_endpoint}/${each.key}_db"
  redis_url    = module.shared.redis_url

  additional_env_vars = each.value.env_vars

  secrets = [
    {
      name      = "DATABASE_PASSWORD"
      valueFrom = "${module.shared.database_secret_arn}:password::"
    }
  ]

  # Shared infrastructure
  vpc_id                      = module.shared.vpc_id
  private_subnet_ids          = module.shared.private_subnet_ids
  ecs_cluster_id              = module.shared.ecs_cluster_id
  ecs_cluster_name            = module.shared.ecs_cluster_name
  alb_listener_arn            = module.shared.alb_listener_arn
  ecs_security_group_id       = module.shared.ecs_security_group_id
  ecs_task_execution_role_arn = module.shared.ecs_task_execution_role_arn
  ecs_task_role_arn           = module.shared.ecs_task_role_arn
  log_group_name              = module.shared.log_group_names[each.key]
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "alb_dns_name" {
  description = "Load balancer DNS - point your domain here"
  value       = module.shared.alb_dns_name
}

output "ecr_repositories" {
  description = "ECR repository URLs - push your Docker images here"
  value       = module.shared.ecr_repository_urls
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = module.shared.database_endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.shared.redis_endpoint
}

output "app_urls" {
  description = "App URLs (once DNS is configured)"
  value = {
    for name, config in local.apps :
    name => config.host_headers != null ? "https://${config.host_headers[0]}" : "Path: ${config.path_patterns[0]}"
  }
}
