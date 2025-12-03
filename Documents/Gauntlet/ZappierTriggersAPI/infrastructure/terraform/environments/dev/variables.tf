# Development Environment Variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "zapier-triggers"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# VPC (using 10.1.x.x to avoid conflict with Flourish which uses 10.0.x.x)
variable "vpc_cidr" {
  type    = string
  default = "10.1.0.0/16"
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.1.1.0/24", "10.1.2.0/24"]
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.1.101.0/24", "10.1.102.0/24"]
}

variable "database_subnet_cidrs" {
  type    = list(string)
  default = ["10.1.201.0/24", "10.1.202.0/24"]
}

variable "enable_nat_gateway" {
  type    = bool
  default = true
}

variable "single_nat_gateway" {
  type    = bool
  default = true  # Single NAT for dev to save costs
}

variable "enable_vpc_endpoints" {
  type    = bool
  default = false  # Disabled for dev to save costs
}

# RDS
variable "rds_instance_class" {
  type    = string
  default = "db.t3.micro"  # Smallest instance for dev
}

variable "rds_allocated_storage" {
  type    = number
  default = 20
}

variable "rds_max_allocated_storage" {
  type    = number
  default = 50
}

variable "rds_db_name" {
  type    = string
  default = "zapier_triggers"
}

variable "rds_multi_az" {
  type    = bool
  default = false  # Single AZ for dev
}

variable "rds_backup_retention_period" {
  type    = number
  default = 1  # Minimal backups for dev
}

variable "rds_deletion_protection" {
  type    = bool
  default = false  # Allow deletion in dev
}

variable "rds_performance_insights_enabled" {
  type    = bool
  default = false  # Disabled for dev
}

# ElastiCache
variable "redis_node_type" {
  type    = string
  default = "cache.t3.micro"  # Smallest instance for dev
}

variable "redis_num_cache_clusters" {
  type    = number
  default = 1  # Single node for dev
}

variable "redis_automatic_failover_enabled" {
  type    = bool
  default = false
}

variable "redis_multi_az_enabled" {
  type    = bool
  default = false
}

variable "redis_at_rest_encryption_enabled" {
  type    = bool
  default = true
}

variable "redis_transit_encryption_enabled" {
  type    = bool
  default = false  # Disabled for dev simplicity
}

variable "redis_snapshot_retention_limit" {
  type    = number
  default = 0  # No snapshots for dev
}

# SQS
variable "sqs_visibility_timeout" {
  type    = number
  default = 30
}

variable "sqs_message_retention_seconds" {
  type    = number
  default = 345600
}

variable "sqs_receive_wait_time" {
  type    = number
  default = 20
}

variable "sqs_max_receive_count" {
  type    = number
  default = 5
}

variable "sqs_enable_priority_queues" {
  type    = bool
  default = false
}

variable "sqs_queue_depth_alarm_threshold" {
  type    = number
  default = 1000
}

# ECS
variable "container_image" {
  type    = string
  default = ""  # Set via tfvars or CI/CD
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "api_cpu" {
  type    = number
  default = 256
}

variable "api_memory" {
  type    = number
  default = 512
}

variable "api_desired_count" {
  type    = number
  default = 1  # Single instance for dev
}

variable "api_min_count" {
  type    = number
  default = 1
}

variable "api_max_count" {
  type    = number
  default = 2
}

variable "worker_cpu" {
  type    = number
  default = 256
}

variable "worker_memory" {
  type    = number
  default = 512
}

variable "worker_desired_count" {
  type    = number
  default = 1
}

variable "worker_min_count" {
  type    = number
  default = 1
}

variable "worker_max_count" {
  type    = number
  default = 2
}

variable "ecs_log_retention_days" {
  type    = number
  default = 7  # Short retention for dev
}

variable "enable_container_insights" {
  type    = bool
  default = false  # Disabled for dev
}

# ALB
variable "certificate_arn" {
  type    = string
  default = ""  # Set via tfvars
}

variable "additional_certificate_arns" {
  type    = list(string)
  default = []
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "enable_alb_access_logs" {
  type    = bool
  default = false  # Disabled for dev
}

variable "alb_access_logs_bucket" {
  type    = string
  default = ""
}

variable "waf_web_acl_arn" {
  type    = string
  default = ""  # No WAF for dev
}

# DNS
variable "route53_zone_id" {
  type    = string
  default = ""
}

variable "domain_name" {
  type    = string
  default = ""
}

# Monitoring
variable "alarm_sns_topic_arn" {
  type    = string
  default = ""
}
