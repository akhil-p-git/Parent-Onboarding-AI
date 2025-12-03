# Production Environment Configuration

terraform {
  backend "s3" {
    bucket         = "zapier-triggers-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "zapier-triggers-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "infrastructure" {
  source = "../../"

  project_name       = var.project_name
  environment        = var.environment
  availability_zones = var.availability_zones

  # VPC
  vpc_cidr              = var.vpc_cidr
  private_subnet_cidrs  = var.private_subnet_cidrs
  public_subnet_cidrs   = var.public_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
  enable_nat_gateway    = var.enable_nat_gateway
  single_nat_gateway    = var.single_nat_gateway
  enable_vpc_endpoints  = var.enable_vpc_endpoints

  # RDS
  rds_instance_class            = var.rds_instance_class
  rds_allocated_storage         = var.rds_allocated_storage
  rds_max_allocated_storage     = var.rds_max_allocated_storage
  rds_db_name                   = var.rds_db_name
  rds_multi_az                  = var.rds_multi_az
  rds_backup_retention_period   = var.rds_backup_retention_period
  rds_deletion_protection       = var.rds_deletion_protection
  rds_performance_insights_enabled = var.rds_performance_insights_enabled

  # ElastiCache
  redis_node_type                  = var.redis_node_type
  redis_num_cache_clusters         = var.redis_num_cache_clusters
  redis_automatic_failover_enabled = var.redis_automatic_failover_enabled
  redis_multi_az_enabled           = var.redis_multi_az_enabled
  redis_at_rest_encryption_enabled = var.redis_at_rest_encryption_enabled
  redis_transit_encryption_enabled = var.redis_transit_encryption_enabled
  redis_snapshot_retention_limit   = var.redis_snapshot_retention_limit

  # SQS
  sqs_visibility_timeout          = var.sqs_visibility_timeout
  sqs_message_retention_seconds   = var.sqs_message_retention_seconds
  sqs_receive_wait_time           = var.sqs_receive_wait_time
  sqs_max_receive_count           = var.sqs_max_receive_count
  sqs_enable_priority_queues      = var.sqs_enable_priority_queues
  sqs_queue_depth_alarm_threshold = var.sqs_queue_depth_alarm_threshold

  # ECS
  container_image       = var.container_image
  container_port        = var.container_port
  api_cpu               = var.api_cpu
  api_memory            = var.api_memory
  api_desired_count     = var.api_desired_count
  api_min_count         = var.api_min_count
  api_max_count         = var.api_max_count
  worker_cpu            = var.worker_cpu
  worker_memory         = var.worker_memory
  worker_desired_count  = var.worker_desired_count
  worker_min_count      = var.worker_min_count
  worker_max_count      = var.worker_max_count
  ecs_log_retention_days = var.ecs_log_retention_days
  enable_container_insights = var.enable_container_insights

  # ALB
  certificate_arn             = var.certificate_arn
  additional_certificate_arns = var.additional_certificate_arns
  health_check_path           = var.health_check_path
  enable_alb_access_logs      = var.enable_alb_access_logs
  alb_access_logs_bucket      = var.alb_access_logs_bucket
  waf_web_acl_arn             = var.waf_web_acl_arn

  # DNS
  route53_zone_id = var.route53_zone_id
  domain_name     = var.domain_name

  # Monitoring
  alarm_sns_topic_arn = var.alarm_sns_topic_arn
}
