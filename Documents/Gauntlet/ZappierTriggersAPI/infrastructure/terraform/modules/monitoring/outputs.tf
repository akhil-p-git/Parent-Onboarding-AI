# Monitoring Module Outputs

output "api_log_group_name" {
  description = "API CloudWatch log group name"
  value       = aws_cloudwatch_log_group.api.name
}

output "api_log_group_arn" {
  description = "API CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.api.arn
}

output "worker_log_group_name" {
  description = "Worker CloudWatch log group name"
  value       = aws_cloudwatch_log_group.worker.name
}

output "worker_log_group_arn" {
  description = "Worker CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.worker.arn
}

output "application_log_group_name" {
  description = "Application CloudWatch log group name"
  value       = aws_cloudwatch_log_group.application.name
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_arn" {
  description = "CloudWatch dashboard ARN"
  value       = aws_cloudwatch_dashboard.main.dashboard_arn
}

output "critical_alarm_arn" {
  description = "Critical composite alarm ARN"
  value       = aws_cloudwatch_composite_alarm.critical.arn
}

output "alarm_arns" {
  description = "Map of all alarm ARNs"
  value = {
    api_error_rate        = aws_cloudwatch_metric_alarm.api_error_rate.arn
    api_latency_p99       = aws_cloudwatch_metric_alarm.api_latency_p99.arn
    api_cpu_high          = aws_cloudwatch_metric_alarm.api_cpu_high.arn
    worker_cpu_high       = aws_cloudwatch_metric_alarm.worker_cpu_high.arn
    events_queue_backup   = aws_cloudwatch_metric_alarm.events_queue_backup.arn
    deliveries_queue_backup = aws_cloudwatch_metric_alarm.deliveries_queue_backup.arn
    events_dlq            = aws_cloudwatch_metric_alarm.events_dlq.arn
    deliveries_dlq        = aws_cloudwatch_metric_alarm.deliveries_dlq.arn
    rds_cpu_high          = aws_cloudwatch_metric_alarm.rds_cpu_high.arn
    rds_storage_low       = aws_cloudwatch_metric_alarm.rds_storage_low.arn
    redis_memory_high     = aws_cloudwatch_metric_alarm.redis_memory_high.arn
  }
}
