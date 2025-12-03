# Root Module Variables

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "zapier-triggers"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# RDS Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage in GB for autoscaling"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "triggers_api"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "triggers_admin"
  sensitive   = true
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

# ElastiCache Configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

# ECS Configuration
variable "ecs_api_cpu" {
  description = "CPU units for API task"
  type        = number
  default     = 256
}

variable "ecs_api_memory" {
  description = "Memory in MB for API task"
  type        = number
  default     = 512
}

variable "ecs_api_desired_count" {
  description = "Desired number of API tasks"
  type        = number
  default     = 2
}

variable "ecs_worker_cpu" {
  description = "CPU units for worker task"
  type        = number
  default     = 256
}

variable "ecs_worker_memory" {
  description = "Memory in MB for worker task"
  type        = number
  default     = 512
}

variable "ecs_worker_desired_count" {
  description = "Desired number of worker tasks"
  type        = number
  default     = 1
}

# Container Configuration
variable "container_image" {
  description = "Docker image for the application"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

# Domain Configuration
variable "domain_name" {
  description = "Domain name for the API"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""
}

# Monitoring
variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring for RDS"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# Additional ECS variables
variable "api_min_count" {
  description = "Minimum API task count"
  type        = number
  default     = 1
}

variable "api_max_count" {
  description = "Maximum API task count"
  type        = number
  default     = 3
}

variable "worker_cpu" {
  description = "CPU units for worker task"
  type        = number
  default     = 256
}

variable "worker_memory" {
  description = "Memory in MB for worker task"
  type        = number
  default     = 512
}

variable "worker_desired_count" {
  description = "Desired number of worker tasks"
  type        = number
  default     = 1
}

variable "worker_min_count" {
  description = "Minimum worker task count"
  type        = number
  default     = 1
}

variable "worker_max_count" {
  description = "Maximum worker task count"
  type        = number
  default     = 2
}

variable "ecs_log_retention_days" {
  description = "ECS log retention in days"
  type        = number
  default     = 7
}

variable "enable_container_insights" {
  description = "Enable container insights"
  type        = bool
  default     = false
}

# ALB variables
variable "enable_alb_access_logs" {
  description = "Enable ALB access logs"
  type        = bool
  default     = false
}

variable "alb_access_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  type        = string
  default     = ""
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for alarms"
  type        = string
  default     = ""
}

# VPC variables
variable "enable_nat_gateway" {
  description = "Enable NAT gateway"
  type        = bool
  default     = true
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints"
  type        = bool
  default     = false
}

# RDS variables
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage"
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "RDS max allocated storage"
  type        = number
  default     = 50
}

variable "rds_db_name" {
  description = "RDS database name"
  type        = string
  default     = "zapier_triggers"
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = false
}

variable "rds_backup_retention_period" {
  description = "RDS backup retention period"
  type        = number
  default     = 1
}

variable "rds_performance_insights_enabled" {
  description = "Enable RDS Performance Insights"
  type        = bool
  default     = false
}

# Redis variables (additional)
variable "redis_num_cache_clusters" {
  description = "Number of Redis cache clusters"
  type        = number
  default     = 1
}

variable "redis_transit_encryption_enabled" {
  description = "Enable Redis transit encryption"
  type        = bool
  default     = false
}

variable "redis_snapshot_retention_limit" {
  description = "Redis snapshot retention limit"
  type        = number
  default     = 0
}

# Route53 variables
variable "route53_zone_id" {
  description = "Route53 zone ID"
  type        = string
  default     = ""
}

# SQS Configuration
variable "sqs_visibility_timeout" {
  description = "SQS visibility timeout in seconds"
  type        = number
  default     = 30
}

variable "sqs_message_retention_seconds" {
  description = "SQS message retention period in seconds"
  type        = number
  default     = 345600  # 4 days
}

variable "sqs_receive_wait_time" {
  description = "SQS long polling wait time in seconds"
  type        = number
  default     = 20
}

variable "sqs_max_receive_count" {
  description = "SQS max receives before sending to DLQ"
  type        = number
  default     = 5
}

variable "sqs_enable_priority_queues" {
  description = "Enable SQS high priority queue"
  type        = bool
  default     = false
}

variable "sqs_queue_depth_alarm_threshold" {
  description = "SQS queue depth threshold for alarm"
  type        = number
  default     = 1000
}

# ALB Configuration
variable "health_check_path" {
  description = "Health check path for ALB target group"
  type        = string
  default     = "/api/v1/health"
}

variable "additional_certificate_arns" {
  description = "Additional ACM certificate ARNs for ALB"
  type        = list(string)
  default     = []
}

variable "waf_web_acl_arn" {
  description = "WAF Web ACL ARN to associate with ALB"
  type        = string
  default     = ""
}

# ECS API Configuration
variable "api_cpu" {
  description = "CPU units for API task"
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "Memory in MB for API task"
  type        = number
  default     = 512
}

variable "api_desired_count" {
  description = "Desired number of API tasks"
  type        = number
  default     = 1
}
