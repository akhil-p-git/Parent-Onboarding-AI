# ECS Module Variables

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

# Networking
variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
}

# Container Configuration
variable "container_image" {
  description = "Docker image for the container"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

# API Service Configuration
variable "api_cpu" {
  description = "API task CPU units"
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "API task memory in MiB"
  type        = number
  default     = 512
}

variable "api_desired_count" {
  description = "Desired count of API tasks"
  type        = number
  default     = 2
}

variable "api_min_count" {
  description = "Minimum count of API tasks"
  type        = number
  default     = 1
}

variable "api_max_count" {
  description = "Maximum count of API tasks"
  type        = number
  default     = 10
}

# Worker Service Configuration
variable "worker_cpu" {
  description = "Worker task CPU units"
  type        = number
  default     = 256
}

variable "worker_memory" {
  description = "Worker task memory in MiB"
  type        = number
  default     = 512
}

variable "worker_desired_count" {
  description = "Desired count of worker tasks"
  type        = number
  default     = 2
}

variable "worker_min_count" {
  description = "Minimum count of worker tasks"
  type        = number
  default     = 1
}

variable "worker_max_count" {
  description = "Maximum count of worker tasks"
  type        = number
  default     = 10
}

# Secrets
variable "db_secret_arn" {
  description = "ARN of database secret"
  type        = string
}

variable "redis_secret_arn" {
  description = "ARN of Redis secret (optional)"
  type        = string
  default     = null
}

variable "redis_url" {
  description = "Redis connection URL (used when redis_secret_arn is not provided)"
  type        = string
  default     = ""
}

variable "secrets_arns" {
  description = "List of secret ARNs for execution role"
  type        = list(string)
  default     = []
}

# SQS
variable "sqs_queue_arns" {
  description = "List of SQS queue ARNs for task role"
  type        = list(string)
  default     = []
}

# Load Balancer
variable "target_group_arn" {
  description = "ALB target group ARN"
  type        = string
}

# Logging
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "enable_container_insights" {
  description = "Enable Container Insights"
  type        = bool
  default     = true
}
