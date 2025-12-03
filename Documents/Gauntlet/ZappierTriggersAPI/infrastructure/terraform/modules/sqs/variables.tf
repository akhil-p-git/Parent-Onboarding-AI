# SQS Module Variables

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "visibility_timeout" {
  description = "Visibility timeout in seconds"
  type        = number
  default     = 30
}

variable "message_retention_seconds" {
  description = "Message retention period in seconds"
  type        = number
  default     = 345600  # 4 days
}

variable "receive_wait_time" {
  description = "Long polling wait time in seconds"
  type        = number
  default     = 20
}

variable "max_receive_count" {
  description = "Max receives before sending to DLQ"
  type        = number
  default     = 5
}

variable "enable_priority_queues" {
  description = "Enable high priority queue"
  type        = bool
  default     = false
}

variable "queue_depth_alarm_threshold" {
  description = "Queue depth threshold for alarm"
  type        = number
  default     = 1000
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for alarms"
  type        = string
  default     = ""
}
