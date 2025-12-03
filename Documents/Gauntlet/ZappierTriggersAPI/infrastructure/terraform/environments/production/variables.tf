# Production Environment Variables

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
  default     = "production"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]  # 3 AZs for production
}

# VPC
variable "vpc_cidr" {
  type    = string
  default = "10.2.0.0/16"
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.2.101.0/24", "10.2.102.0/24", "10.2.103.0/24"]
}

variable "database_subnet_cidrs" {
  type    = list(string)
  default = ["10.2.201.0/24", "10.2.202.0/24", "10.2.203.0/24"]
}

variable "enable_nat_gateway" {
  type    = bool
  default = true
}

variable "single_nat_gateway" {
  type    = bool
  default = false  # NAT per AZ for production HA
}

variable "enable_vpc_endpoints" {
  type    = bool
  default = true
}

# RDS
variable "rds_instance_class" {
  type    = string
  default = "db.r6g.large"  # Production-grade instance
}

variable "rds_allocated_storage" {
  type    = number
  default = 100
}

variable "rds_max_allocated_storage" {
  type    = number
  default = 500
}

variable "rds_db_name" {
  type    = string
  default = "zapier_triggers"
}

variable "rds_multi_az" {
  type    = bool
  default = true  # Multi-AZ for production
}

variable "rds_backup_retention_period" {
  type    = number
  default = 30  # 30 days for production
}

variable "rds_deletion_protection" {
  type    = bool
  default = true
}

variable "rds_performance_insights_enabled" {
  type    = bool
  default = true
}

# ElastiCache
variable "redis_node_type" {
  type    = string
  default = "cache.r6g.large"  # Production-grade instance
}

variable "redis_num_cache_clusters" {
  type    = number
  default = 3  # Primary + 2 replicas
}

variable "redis_automatic_failover_enabled" {
  type    = bool
  default = true
}

variable "redis_multi_az_enabled" {
  type    = bool
  default = true
}

variable "redis_at_rest_encryption_enabled" {
  type    = bool
  default = true
}

variable "redis_transit_encryption_enabled" {
  type    = bool
  default = true
}

variable "redis_snapshot_retention_limit" {
  type    = number
  default = 7
}

# SQS
variable "sqs_visibility_timeout" {
  type    = number
  default = 30
}

variable "sqs_message_retention_seconds" {
  type    = number
  default = 604800  # 7 days for production
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
  default = true
}

variable "sqs_queue_depth_alarm_threshold" {
  type    = number
  default = 500
}

# ECS
variable "container_image" {
  type    = string
  default = ""
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "api_cpu" {
  type    = number
  default = 1024
}

variable "api_memory" {
  type    = number
  default = 2048
}

variable "api_desired_count" {
  type    = number
  default = 3
}

variable "api_min_count" {
  type    = number
  default = 3
}

variable "api_max_count" {
  type    = number
  default = 20
}

variable "worker_cpu" {
  type    = number
  default = 1024
}

variable "worker_memory" {
  type    = number
  default = 2048
}

variable "worker_desired_count" {
  type    = number
  default = 3
}

variable "worker_min_count" {
  type    = number
  default = 3
}

variable "worker_max_count" {
  type    = number
  default = 20
}

variable "ecs_log_retention_days" {
  type    = number
  default = 90
}

variable "enable_container_insights" {
  type    = bool
  default = true
}

# ALB
variable "certificate_arn" {
  type    = string
  default = ""
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
  default = true
}

variable "alb_access_logs_bucket" {
  type    = string
  default = ""
}

variable "waf_web_acl_arn" {
  type    = string
  default = ""  # Strongly recommended for production
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
