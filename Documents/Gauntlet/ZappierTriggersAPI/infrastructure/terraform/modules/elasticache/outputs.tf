# ElastiCache Module Outputs

output "replication_group_id" {
  description = "ElastiCache replication group ID"
  value       = aws_elasticache_replication_group.main.id
}

output "primary_endpoint_address" {
  description = "Primary endpoint address"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "Reader endpoint address"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "port" {
  description = "Redis port"
  value       = 6379
}

output "redis_url" {
  description = "Redis connection URL (without auth token)"
  value       = "redis://${aws_elasticache_replication_group.main.primary_endpoint_address}:6379"
}

output "auth_token_secret_arn" {
  description = "Secrets Manager secret ARN for auth token"
  value       = var.transit_encryption_enabled ? aws_secretsmanager_secret.redis_auth[0].arn : null
}
