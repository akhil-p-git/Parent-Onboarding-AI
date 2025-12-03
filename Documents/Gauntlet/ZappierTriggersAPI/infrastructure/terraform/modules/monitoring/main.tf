# Monitoring Module - CloudWatch Dashboards, Alarms, and Log Groups

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# =============================================================================
# CloudWatch Log Groups
# =============================================================================

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name_prefix}/api"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${local.name_prefix}-api-logs"
    Service     = "api"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${local.name_prefix}/worker"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${local.name_prefix}-worker-logs"
    Service     = "worker"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/application/${local.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${local.name_prefix}-app-logs"
    Environment = var.environment
  }
}

# Log Metric Filters for error tracking
resource "aws_cloudwatch_log_metric_filter" "api_errors" {
  name           = "${local.name_prefix}-api-errors"
  pattern        = "[timestamp, request_id, level=\"ERROR\", ...]"
  log_group_name = aws_cloudwatch_log_group.api.name

  metric_transformation {
    name          = "APIErrors"
    namespace     = "${local.name_prefix}/Application"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "api_4xx_errors" {
  name           = "${local.name_prefix}-api-4xx"
  pattern        = "{ $.status_code >= 400 && $.status_code < 500 }"
  log_group_name = aws_cloudwatch_log_group.api.name

  metric_transformation {
    name          = "API4xxErrors"
    namespace     = "${local.name_prefix}/Application"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "api_5xx_errors" {
  name           = "${local.name_prefix}-api-5xx"
  pattern        = "{ $.status_code >= 500 }"
  log_group_name = aws_cloudwatch_log_group.api.name

  metric_transformation {
    name          = "API5xxErrors"
    namespace     = "${local.name_prefix}/Application"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "worker_errors" {
  name           = "${local.name_prefix}-worker-errors"
  pattern        = "[timestamp, request_id, level=\"ERROR\", ...]"
  log_group_name = aws_cloudwatch_log_group.worker.name

  metric_transformation {
    name          = "WorkerErrors"
    namespace     = "${local.name_prefix}/Application"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "webhook_delivery_failures" {
  name           = "${local.name_prefix}-webhook-failures"
  pattern        = "{ $.event = \"webhook_delivery_failed\" }"
  log_group_name = aws_cloudwatch_log_group.worker.name

  metric_transformation {
    name          = "WebhookDeliveryFailures"
    namespace     = "${local.name_prefix}/Application"
    value         = "1"
    default_value = "0"
  }
}

# =============================================================================
# CloudWatch Dashboard
# =============================================================================

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name_prefix}-overview"

  dashboard_body = jsonencode({
    widgets = [
      # Row 1: API Metrics
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# API Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 6
        height = 6
        properties = {
          title  = "API Request Rate"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", period = 60 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 1
        width  = 6
        height = 6
        properties = {
          title  = "API Response Time (p50, p90, p99)"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix, { stat = "p50", period = 60 }],
            ["...", { stat = "p90", period = 60 }],
            ["...", { stat = "p99", period = 60 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 1
        width  = 6
        height = 6
        properties = {
          title  = "HTTP Errors"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_ELB_4XX_Count", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", period = 60, color = "#ff7f0e" }],
            ["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", period = 60, color = "#d62728" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", period = 60, color = "#ffbb78" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", period = 60, color = "#ff9896" }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 1
        width  = 6
        height = 6
        properties = {
          title  = "Healthy Hosts"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "HealthyHostCount", "TargetGroup", var.target_group_arn_suffix, "LoadBalancer", var.alb_arn_suffix],
            ["AWS/ApplicationELB", "UnHealthyHostCount", "TargetGroup", var.target_group_arn_suffix, "LoadBalancer", var.alb_arn_suffix, { color = "#d62728" }]
          ]
          view = "timeSeries"
        }
      },

      # Row 2: ECS Metrics
      {
        type   = "text"
        x      = 0
        y      = 7
        width  = 24
        height = 1
        properties = {
          markdown = "# ECS Service Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 8
        width  = 6
        height = 6
        properties = {
          title  = "API Service CPU"
          region = var.aws_region
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.api_service_name, "ClusterName", var.ecs_cluster_name, { stat = "Average", period = 60 }]
          ]
          view       = "timeSeries"
          yAxis      = { left = { min = 0, max = 100 } }
          annotations = {
            horizontal = [{ value = 70, color = "#ff7f0e", label = "Scale Out Threshold" }]
          }
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 8
        width  = 6
        height = 6
        properties = {
          title  = "API Service Memory"
          region = var.aws_region
          metrics = [
            ["AWS/ECS", "MemoryUtilization", "ServiceName", var.api_service_name, "ClusterName", var.ecs_cluster_name, { stat = "Average", period = 60 }]
          ]
          view       = "timeSeries"
          yAxis      = { left = { min = 0, max = 100 } }
          annotations = {
            horizontal = [{ value = 80, color = "#ff7f0e", label = "Scale Out Threshold" }]
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 8
        width  = 6
        height = 6
        properties = {
          title  = "Worker Service CPU"
          region = var.aws_region
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.worker_service_name, "ClusterName", var.ecs_cluster_name, { stat = "Average", period = 60 }]
          ]
          view  = "timeSeries"
          yAxis = { left = { min = 0, max = 100 } }
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 8
        width  = 6
        height = 6
        properties = {
          title  = "Running Tasks"
          region = var.aws_region
          metrics = [
            ["ECS/ContainerInsights", "RunningTaskCount", "ServiceName", var.api_service_name, "ClusterName", var.ecs_cluster_name, { label = "API Tasks" }],
            ["ECS/ContainerInsights", "RunningTaskCount", "ServiceName", var.worker_service_name, "ClusterName", var.ecs_cluster_name, { label = "Worker Tasks" }]
          ]
          view = "timeSeries"
        }
      },

      # Row 3: Queue Metrics
      {
        type   = "text"
        x      = 0
        y      = 14
        width  = 24
        height = 1
        properties = {
          markdown = "# Queue Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 15
        width  = 8
        height = 6
        properties = {
          title  = "Events Queue Depth"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.events_queue_name, { label = "Visible" }],
            ["AWS/SQS", "ApproximateNumberOfMessagesNotVisible", "QueueName", var.events_queue_name, { label = "In Flight" }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 15
        width  = 8
        height = 6
        properties = {
          title  = "Deliveries Queue Depth"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.deliveries_queue_name, { label = "Visible" }],
            ["AWS/SQS", "ApproximateNumberOfMessagesNotVisible", "QueueName", var.deliveries_queue_name, { label = "In Flight" }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 15
        width  = 8
        height = 6
        properties = {
          title  = "DLQ Messages"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.events_dlq_name, { label = "Events DLQ", color = "#d62728" }],
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.deliveries_dlq_name, { label = "Deliveries DLQ", color = "#ff7f0e" }]
          ]
          view = "timeSeries"
        }
      },

      # Row 4: Database Metrics
      {
        type   = "text"
        x      = 0
        y      = 21
        width  = 24
        height = 1
        properties = {
          markdown = "# Database Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 22
        width  = 6
        height = 6
        properties = {
          title  = "RDS CPU"
          region = var.aws_region
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.rds_instance_id, { stat = "Average", period = 60 }]
          ]
          view  = "timeSeries"
          yAxis = { left = { min = 0, max = 100 } }
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 22
        width  = 6
        height = 6
        properties = {
          title  = "RDS Connections"
          region = var.aws_region
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", var.rds_instance_id, { stat = "Average", period = 60 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 22
        width  = 6
        height = 6
        properties = {
          title  = "Redis CPU"
          region = var.aws_region
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", var.redis_cluster_id, { stat = "Average", period = 60 }]
          ]
          view  = "timeSeries"
          yAxis = { left = { min = 0, max = 100 } }
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 22
        width  = 6
        height = 6
        properties = {
          title  = "Redis Memory"
          region = var.aws_region
          metrics = [
            ["AWS/ElastiCache", "DatabaseMemoryUsagePercentage", "CacheClusterId", var.redis_cluster_id, { stat = "Average", period = 60 }]
          ]
          view  = "timeSeries"
          yAxis = { left = { min = 0, max = 100 } }
        }
      }
    ]
  })
}

# =============================================================================
# CloudWatch Alarms
# =============================================================================

# API Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "api_error_rate" {
  alarm_name          = "${local.name_prefix}-api-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = var.error_rate_threshold

  metric_query {
    id          = "error_rate"
    expression  = "(errors / requests) * 100"
    label       = "Error Rate %"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      metric_name = "HTTPCode_Target_5XX_Count"
      namespace   = "AWS/ApplicationELB"
      period      = 300
      stat        = "Sum"
      dimensions = {
        LoadBalancer = var.alb_arn_suffix
      }
    }
  }

  metric_query {
    id = "requests"
    metric {
      metric_name = "RequestCount"
      namespace   = "AWS/ApplicationELB"
      period      = 300
      stat        = "Sum"
      dimensions = {
        LoadBalancer = var.alb_arn_suffix
      }
    }
  }

  alarm_description = "API error rate exceeds ${var.error_rate_threshold}%"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
  ok_actions        = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-api-error-rate-alarm"
  }
}

# API Latency Alarm (p99)
resource "aws_cloudwatch_metric_alarm" "api_latency_p99" {
  alarm_name          = "${local.name_prefix}-api-latency-p99"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  extended_statistic  = "p99"
  threshold           = var.latency_threshold_p99

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_description = "API p99 latency exceeds ${var.latency_threshold_p99}s"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
  ok_actions        = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-api-latency-alarm"
  }
}

# ECS API Service CPU Alarm
resource "aws_cloudwatch_metric_alarm" "api_cpu_high" {
  alarm_name          = "${local.name_prefix}-api-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.api_service_name
  }

  alarm_description = "API service CPU utilization is high"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-api-cpu-alarm"
  }
}

# ECS Worker Service CPU Alarm
resource "aws_cloudwatch_metric_alarm" "worker_cpu_high" {
  alarm_name          = "${local.name_prefix}-worker-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.worker_service_name
  }

  alarm_description = "Worker service CPU utilization is high"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-worker-cpu-alarm"
  }
}

# Events Queue Backup Alarm
resource "aws_cloudwatch_metric_alarm" "events_queue_backup" {
  alarm_name          = "${local.name_prefix}-events-queue-backup"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = var.queue_backup_threshold

  dimensions = {
    QueueName = var.events_queue_name
  }

  alarm_description = "Events queue has ${var.queue_backup_threshold}+ messages backed up"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
  ok_actions        = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-events-queue-backup-alarm"
  }
}

# Deliveries Queue Backup Alarm
resource "aws_cloudwatch_metric_alarm" "deliveries_queue_backup" {
  alarm_name          = "${local.name_prefix}-deliveries-queue-backup"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = var.queue_backup_threshold

  dimensions = {
    QueueName = var.deliveries_queue_name
  }

  alarm_description = "Deliveries queue has ${var.queue_backup_threshold}+ messages backed up"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
  ok_actions        = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-deliveries-queue-backup-alarm"
  }
}

# DLQ Messages Alarm (Events)
resource "aws_cloudwatch_metric_alarm" "events_dlq" {
  alarm_name          = "${local.name_prefix}-events-dlq"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0

  dimensions = {
    QueueName = var.events_dlq_name
  }

  alarm_description = "Messages in events DLQ - requires investigation"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-events-dlq-alarm"
  }
}

# DLQ Messages Alarm (Deliveries)
resource "aws_cloudwatch_metric_alarm" "deliveries_dlq" {
  alarm_name          = "${local.name_prefix}-deliveries-dlq"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 10

  dimensions = {
    QueueName = var.deliveries_dlq_name
  }

  alarm_description = "Messages accumulating in deliveries DLQ"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-deliveries-dlq-alarm"
  }
}

# RDS CPU Alarm
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  alarm_description = "RDS CPU utilization is high"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-rds-cpu-alarm"
  }
}

# RDS Free Storage Alarm
resource "aws_cloudwatch_metric_alarm" "rds_storage_low" {
  alarm_name          = "${local.name_prefix}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120  # 5 GB in bytes

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  alarm_description = "RDS free storage is below 5GB"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-rds-storage-alarm"
  }
}

# Redis Memory Alarm
resource "aws_cloudwatch_metric_alarm" "redis_memory_high" {
  alarm_name          = "${local.name_prefix}-redis-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    CacheClusterId = var.redis_cluster_id
  }

  alarm_description = "Redis memory usage is high"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${local.name_prefix}-redis-memory-alarm"
  }
}

# Composite Alarm for Critical Issues
resource "aws_cloudwatch_composite_alarm" "critical" {
  alarm_name = "${local.name_prefix}-critical"

  alarm_rule = join(" OR ", [
    "ALARM(${aws_cloudwatch_metric_alarm.api_error_rate.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.events_dlq.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.rds_storage_low.alarm_name})",
  ])

  alarm_description = "Critical alarm - one or more critical conditions detected"
  alarm_actions     = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
  ok_actions        = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name     = "${local.name_prefix}-critical-alarm"
    Severity = "critical"
  }
}
