# App Module Outputs

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.app.name
}

output "service_arn" {
  description = "ECS service ARN"
  value       = aws_ecs_service.app.id
}

output "task_definition_arn" {
  description = "Task definition ARN"
  value       = aws_ecs_task_definition.app.arn
}

output "target_group_arn" {
  description = "Target group ARN"
  value       = aws_lb_target_group.app.arn
}

output "queue_url" {
  description = "SQS queue URL"
  value       = var.enable_queue ? aws_sqs_queue.main[0].url : null
}

output "dlq_url" {
  description = "SQS DLQ URL"
  value       = var.enable_queue ? aws_sqs_queue.dlq[0].url : null
}
