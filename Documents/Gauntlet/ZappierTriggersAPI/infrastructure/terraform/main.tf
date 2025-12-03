# Root Terraform Configuration
# Orchestrates all modules for the Zapier Triggers API infrastructure

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  # Collect all secret ARNs for ECS execution role
  secrets_arns = compact([
    module.rds.db_password_secret_arn,
    module.elasticache.auth_token_secret_arn,
  ])
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = data.aws_region.current.name
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones

  enable_nat_gateway   = var.enable_nat_gateway
  enable_vpc_endpoints = var.enable_vpc_endpoints
  container_port       = var.container_port
}

# RDS Module
module "rds" {
  source = "./modules/rds"

  project_name = var.project_name
  environment  = var.environment

  db_subnet_group_name      = module.vpc.db_subnet_group_name
  security_group_id         = module.vpc.rds_security_group_id

  db_instance_class         = var.rds_instance_class
  db_allocated_storage      = var.rds_allocated_storage
  db_max_allocated_storage  = var.rds_max_allocated_storage
  db_name                   = var.rds_db_name
  db_username               = "triggers_admin"
  multi_az                  = var.rds_multi_az
  backup_retention_period   = var.rds_backup_retention_period
  enable_performance_insights = var.rds_performance_insights_enabled
  alarm_sns_topic_arn       = var.alarm_sns_topic_arn
}

# ElastiCache Module
module "elasticache" {
  source = "./modules/elasticache"

  project_name = var.project_name
  environment  = var.environment

  subnet_group_name          = module.vpc.elasticache_subnet_group_name
  security_group_id          = module.vpc.elasticache_security_group_id

  node_type                  = var.redis_node_type
  num_cache_clusters         = var.redis_num_cache_clusters
  transit_encryption_enabled = var.redis_transit_encryption_enabled
  snapshot_retention_limit   = var.redis_snapshot_retention_limit
  alarm_sns_topic_arn        = var.alarm_sns_topic_arn
}

# SQS Module
module "sqs" {
  source = "./modules/sqs"

  project_name = var.project_name
  environment  = var.environment

  visibility_timeout        = var.sqs_visibility_timeout
  message_retention_seconds = var.sqs_message_retention_seconds
  receive_wait_time         = var.sqs_receive_wait_time
  max_receive_count         = var.sqs_max_receive_count
  enable_priority_queues    = var.sqs_enable_priority_queues
  queue_depth_alarm_threshold = var.sqs_queue_depth_alarm_threshold
  alarm_sns_topic_arn       = var.alarm_sns_topic_arn
}

# ALB Module
module "alb" {
  source = "./modules/alb"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.vpc.alb_security_group_id
  container_port        = var.container_port
  health_check_path     = var.health_check_path
  certificate_arn       = var.certificate_arn
  additional_certificate_arns = var.additional_certificate_arns
  enable_access_logs    = var.enable_alb_access_logs
  access_logs_bucket    = var.alb_access_logs_bucket
  waf_web_acl_arn       = var.waf_web_acl_arn
  alarm_sns_topic_arn   = var.alarm_sns_topic_arn
}

# ECS Module
module "ecs" {
  source = "./modules/ecs"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = data.aws_region.current.name

  private_subnet_ids    = module.vpc.private_subnet_ids
  ecs_security_group_id = module.vpc.ecs_tasks_security_group_id
  target_group_arn      = module.alb.target_group_arn

  container_image = var.container_image
  container_port  = var.container_port

  # API Service
  api_cpu           = var.api_cpu
  api_memory        = var.api_memory
  api_desired_count = var.api_desired_count
  api_min_count     = var.api_min_count
  api_max_count     = var.api_max_count

  # Worker Service
  worker_cpu           = var.worker_cpu
  worker_memory        = var.worker_memory
  worker_desired_count = var.worker_desired_count
  worker_min_count     = var.worker_min_count
  worker_max_count     = var.worker_max_count

  # Secrets
  db_secret_arn    = module.rds.db_password_secret_arn
  redis_secret_arn = module.elasticache.auth_token_secret_arn
  redis_url        = module.elasticache.redis_url
  secrets_arns     = local.secrets_arns
  sqs_queue_arns   = module.sqs.all_queue_arns

  # Logging
  log_retention_days        = var.ecs_log_retention_days
  enable_container_insights = var.enable_container_insights
}

# Route53 Record (optional)
resource "aws_route53_record" "api" {
  count   = var.route53_zone_id != "" ? 1 : 0
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = module.alb.alb_dns_name
    zone_id                = module.alb.alb_zone_id
    evaluate_target_health = true
  }
}

# S3 Bucket for ALB Access Logs
resource "aws_s3_bucket" "alb_logs" {
  count  = var.enable_alb_access_logs && var.alb_access_logs_bucket == "" ? 1 : 0
  bucket = "${local.name_prefix}-alb-logs"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb-logs"
  })
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  count  = var.enable_alb_access_logs && var.alb_access_logs_bucket == "" ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id

  rule {
    id     = "expire-logs"
    status = "Enabled"

    expiration {
      days = 90
    }
  }
}

resource "aws_s3_bucket_policy" "alb_logs" {
  count  = var.enable_alb_access_logs && var.alb_access_logs_bucket == "" ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs[0].arn}/*"
      }
    ]
  })
}

# SNS Topic for Alarms
resource "aws_sns_topic" "alarms" {
  count = var.alarm_sns_topic_arn == "" ? 1 : 0
  name  = "${local.name_prefix}-alarms"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alarms"
  })
}

# Frontend S3 Module
module "frontend_s3" {
  source = "./modules/frontend-s3"

  project_name = var.project_name
  environment  = var.environment
}

# CloudFront Module
module "cloudfront" {
  source = "./modules/cloudfront"

  project_name                   = var.project_name
  environment                    = var.environment
  s3_bucket_id                   = module.frontend_s3.bucket_id
  s3_bucket_arn                  = module.frontend_s3.bucket_arn
  s3_bucket_regional_domain_name = module.frontend_s3.bucket_regional_domain_name
}
