# Root Module Outputs

# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_instance_endpoint
}

output "rds_secret_arn" {
  description = "RDS secret ARN"
  value       = module.rds.db_password_secret_arn
  sensitive   = true
}

# ElastiCache Outputs
output "redis_primary_endpoint" {
  description = "Redis primary endpoint"
  value       = module.elasticache.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint"
  value       = module.elasticache.reader_endpoint_address
}

# SQS Outputs
output "events_queue_url" {
  description = "Events queue URL"
  value       = module.sqs.events_queue_url
}

output "deliveries_queue_url" {
  description = "Deliveries queue URL"
  value       = module.sqs.deliveries_queue_url
}

# ALB Outputs
output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "ALB hosted zone ID"
  value       = module.alb.alb_zone_id
}

output "api_url" {
  description = "API URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${module.alb.alb_dns_name}"
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_api_service_name" {
  description = "ECS API service name"
  value       = module.ecs.api_service_name
}

output "ecs_worker_service_name" {
  description = "ECS worker service name"
  value       = module.ecs.worker_service_name
}

# Useful for CI/CD
output "ecr_repository_url" {
  description = "ECR repository URL (needs to be created separately or passed in)"
  value       = var.container_image
}

output "aws_region" {
  description = "AWS region"
  value       = data.aws_region.current.name
}

output "account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

# Frontend Outputs
output "frontend_bucket_id" {
  description = "Frontend S3 bucket ID"
  value       = module.frontend_s3.bucket_id
}

output "frontend_bucket_arn" {
  description = "Frontend S3 bucket ARN"
  value       = module.frontend_s3.bucket_arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.cloudfront.distribution_domain_name
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "https://${module.cloudfront.distribution_domain_name}"
}
