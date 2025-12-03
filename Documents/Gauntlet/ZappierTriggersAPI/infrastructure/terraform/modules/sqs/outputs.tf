# SQS Module Outputs

output "events_queue_url" {
  description = "Events queue URL"
  value       = aws_sqs_queue.events.url
}

output "events_queue_arn" {
  description = "Events queue ARN"
  value       = aws_sqs_queue.events.arn
}

output "events_queue_name" {
  description = "Events queue name"
  value       = aws_sqs_queue.events.name
}

output "events_dlq_url" {
  description = "Events DLQ URL"
  value       = aws_sqs_queue.events_dlq.url
}

output "events_dlq_arn" {
  description = "Events DLQ ARN"
  value       = aws_sqs_queue.events_dlq.arn
}

output "deliveries_queue_url" {
  description = "Deliveries queue URL"
  value       = aws_sqs_queue.deliveries.url
}

output "deliveries_queue_arn" {
  description = "Deliveries queue ARN"
  value       = aws_sqs_queue.deliveries.arn
}

output "deliveries_dlq_url" {
  description = "Deliveries DLQ URL"
  value       = aws_sqs_queue.deliveries_dlq.url
}

output "deliveries_dlq_arn" {
  description = "Deliveries DLQ ARN"
  value       = aws_sqs_queue.deliveries_dlq.arn
}

output "high_priority_queue_url" {
  description = "High priority queue URL"
  value       = var.enable_priority_queues ? aws_sqs_queue.high_priority[0].url : null
}

output "all_queue_arns" {
  description = "List of all queue ARNs for IAM policies"
  value = compact([
    aws_sqs_queue.events.arn,
    aws_sqs_queue.events_dlq.arn,
    aws_sqs_queue.deliveries.arn,
    aws_sqs_queue.deliveries_dlq.arn,
    var.enable_priority_queues ? aws_sqs_queue.high_priority[0].arn : "",
  ])
}
