# Production Environment Outputs

output "vpc_id" {
  description = "VPC ID"
  value       = module.infrastructure.vpc_id
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.infrastructure.alb_dns_name
}

output "api_url" {
  description = "API URL"
  value       = module.infrastructure.api_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.infrastructure.ecs_cluster_name
}

output "ecs_api_service_name" {
  description = "ECS API service name"
  value       = module.infrastructure.ecs_api_service_name
}

output "ecs_worker_service_name" {
  description = "ECS worker service name"
  value       = module.infrastructure.ecs_worker_service_name
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.infrastructure.rds_endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.infrastructure.redis_primary_endpoint
}

output "events_queue_url" {
  description = "Events queue URL"
  value       = module.infrastructure.events_queue_url
}

output "deliveries_queue_url" {
  description = "Deliveries queue URL"
  value       = module.infrastructure.deliveries_queue_url
}
