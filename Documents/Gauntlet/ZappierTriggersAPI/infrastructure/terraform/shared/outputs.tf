# Shared Infrastructure Outputs
# These values are used by individual app deployments

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

output "ecs_cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.shared.id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.shared.name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.shared.arn
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.shared.dns_name
}

output "alb_zone_id" {
  description = "ALB zone ID for Route53"
  value       = aws_lb.shared.zone_id
}

output "alb_listener_arn" {
  description = "ALB HTTPS listener ARN (or HTTP if no cert)"
  value       = var.certificate_arn != "" ? aws_lb_listener.https[0].arn : aws_lb_listener.http_direct[0].arn
}

output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ECS tasks security group ID"
  value       = aws_security_group.ecs_tasks.id
}

output "database_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.shared.endpoint
}

output "database_name" {
  description = "Default database name"
  value       = aws_db_instance.shared.db_name
}

output "database_secret_arn" {
  description = "Database credentials secret ARN"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = aws_elasticache_replication_group.shared.primary_endpoint_address
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.shared.port
}

output "ecs_task_execution_role_arn" {
  description = "ECS task execution role ARN"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN"
  value       = aws_iam_role.ecs_task.arn
}

output "ecr_repository_urls" {
  description = "ECR repository URLs for each app"
  value       = { for k, v in aws_ecr_repository.apps : k => v.repository_url }
}

output "log_group_names" {
  description = "CloudWatch log group names for each app"
  value       = { for k, v in aws_cloudwatch_log_group.apps : k => v.name }
}

# Connection strings for apps
output "database_url" {
  description = "Database connection URL (without password)"
  value       = "postgresql://postgres:PASSWORD@${aws_db_instance.shared.endpoint}/APP_DB_NAME"
  sensitive   = false
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${aws_elasticache_replication_group.shared.primary_endpoint_address}:${aws_elasticache_replication_group.shared.port}"
}
