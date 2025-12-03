# App Module Variables

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "app_name" {
  description = "Application name"
  type        = string
}

# Container
variable "container_image" {
  description = "Docker image to deploy"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

variable "cpu" {
  description = "CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Memory in MB"
  type        = number
  default     = 512
}

# Scaling
variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

variable "min_count" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "max_count" {
  description = "Maximum number of tasks"
  type        = number
  default     = 4
}

variable "enable_autoscaling" {
  description = "Enable auto scaling"
  type        = bool
  default     = false
}

# Health check
variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/health"
}

# Routing
variable "listener_priority" {
  description = "ALB listener rule priority (1-50000)"
  type        = number
}

variable "host_headers" {
  description = "Host headers for routing (e.g., ['app.example.com'])"
  type        = list(string)
  default     = null
}

variable "path_patterns" {
  description = "Path patterns for routing (e.g., ['/api/*'])"
  type        = list(string)
  default     = null
}

# Queue
variable "enable_queue" {
  description = "Create SQS queue for this app"
  type        = bool
  default     = false
}

variable "queue_visibility_timeout" {
  description = "Queue visibility timeout in seconds"
  type        = number
  default     = 30
}

variable "queue_retention_seconds" {
  description = "Queue message retention in seconds"
  type        = number
  default     = 345600  # 4 days
}

variable "queue_max_receive_count" {
  description = "Max receives before DLQ"
  type        = number
  default     = 5
}

# Environment
variable "database_url" {
  description = "Database connection URL"
  type        = string
}

variable "redis_url" {
  description = "Redis connection URL"
  type        = string
}

variable "additional_env_vars" {
  description = "Additional environment variables"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "secrets" {
  description = "Secrets from AWS Secrets Manager"
  type = list(object({
    name      = string
    valueFrom = string
  }))
  default = []
}

# Shared infrastructure references
variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "ecs_cluster_id" {
  description = "ECS cluster ID"
  type        = string
}

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "alb_listener_arn" {
  description = "ALB listener ARN"
  type        = string
}

variable "ecs_security_group_id" {
  description = "ECS security group ID"
  type        = string
}

variable "ecs_task_execution_role_arn" {
  description = "ECS task execution role ARN"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ECS task role ARN"
  type        = string
}

variable "log_group_name" {
  description = "CloudWatch log group name"
  type        = string
}
