# Monitoring Module Variables

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

# Log Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# ALB
variable "alb_arn_suffix" {
  description = "ALB ARN suffix for metrics"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix for metrics"
  type        = string
}

# ECS
variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "api_service_name" {
  description = "API ECS service name"
  type        = string
}

variable "worker_service_name" {
  description = "Worker ECS service name"
  type        = string
}

# SQS
variable "events_queue_name" {
  description = "Events queue name"
  type        = string
}

variable "deliveries_queue_name" {
  description = "Deliveries queue name"
  type        = string
}

variable "events_dlq_name" {
  description = "Events DLQ name"
  type        = string
}

variable "deliveries_dlq_name" {
  description = "Deliveries DLQ name"
  type        = string
}

# RDS
variable "rds_instance_id" {
  description = "RDS instance identifier"
  type        = string
}

# Redis
variable "redis_cluster_id" {
  description = "ElastiCache cluster ID"
  type        = string
}

# Alarm Thresholds
variable "error_rate_threshold" {
  description = "Error rate percentage threshold for alarm"
  type        = number
  default     = 5
}

variable "latency_threshold_p99" {
  description = "P99 latency threshold in seconds"
  type        = number
  default     = 2.0
}

variable "queue_backup_threshold" {
  description = "Queue message count threshold for backup alarm"
  type        = number
  default     = 1000
}

# SNS
variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  type        = string
  default     = ""
}
