# SQS Module - Message Queues

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# Main Events Queue
resource "aws_sqs_queue" "events" {
  name                       = "${local.name_prefix}-events"
  visibility_timeout_seconds = var.visibility_timeout
  message_retention_seconds  = var.message_retention_seconds
  max_message_size           = 262144  # 256 KB
  delay_seconds              = 0
  receive_wait_time_seconds  = var.receive_wait_time

  # Dead Letter Queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.events_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  # Encryption
  sqs_managed_sse_enabled = true

  tags = {
    Name = "${local.name_prefix}-events"
  }
}

# Events Dead Letter Queue
resource "aws_sqs_queue" "events_dlq" {
  name                       = "${local.name_prefix}-events-dlq"
  message_retention_seconds  = 1209600  # 14 days
  visibility_timeout_seconds = 300

  sqs_managed_sse_enabled = true

  tags = {
    Name = "${local.name_prefix}-events-dlq"
  }
}

# Deliveries Queue
resource "aws_sqs_queue" "deliveries" {
  name                       = "${local.name_prefix}-deliveries"
  visibility_timeout_seconds = 120  # 2 minutes for webhook delivery
  message_retention_seconds  = var.message_retention_seconds
  max_message_size           = 262144
  delay_seconds              = 0
  receive_wait_time_seconds  = var.receive_wait_time

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.deliveries_dlq.arn
    maxReceiveCount     = 3  # Fewer retries, webhook has its own retry
  })

  sqs_managed_sse_enabled = true

  tags = {
    Name = "${local.name_prefix}-deliveries"
  }
}

# Deliveries Dead Letter Queue
resource "aws_sqs_queue" "deliveries_dlq" {
  name                       = "${local.name_prefix}-deliveries-dlq"
  message_retention_seconds  = 1209600
  visibility_timeout_seconds = 300

  sqs_managed_sse_enabled = true

  tags = {
    Name = "${local.name_prefix}-deliveries-dlq"
  }
}

# High Priority Queue (optional)
resource "aws_sqs_queue" "high_priority" {
  count                      = var.enable_priority_queues ? 1 : 0
  name                       = "${local.name_prefix}-events-high-priority"
  visibility_timeout_seconds = var.visibility_timeout
  message_retention_seconds  = var.message_retention_seconds
  delay_seconds              = 0
  receive_wait_time_seconds  = var.receive_wait_time

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.events_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  sqs_managed_sse_enabled = true

  tags = {
    Name = "${local.name_prefix}-events-high-priority"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "events_queue_depth" {
  alarm_name          = "${local.name_prefix}-events-queue-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Average"
  threshold           = var.queue_depth_alarm_threshold
  alarm_description   = "Events queue depth is high"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    QueueName = aws_sqs_queue.events.name
  }

  tags = {
    Name = "${local.name_prefix}-events-queue-depth-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "events_dlq_messages" {
  alarm_name          = "${local.name_prefix}-events-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Messages in events DLQ"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    QueueName = aws_sqs_queue.events_dlq.name
  }

  tags = {
    Name = "${local.name_prefix}-events-dlq-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "deliveries_dlq_messages" {
  alarm_name          = "${local.name_prefix}-deliveries-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Messages accumulating in deliveries DLQ"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    QueueName = aws_sqs_queue.deliveries_dlq.name
  }

  tags = {
    Name = "${local.name_prefix}-deliveries-dlq-alarm"
  }
}
