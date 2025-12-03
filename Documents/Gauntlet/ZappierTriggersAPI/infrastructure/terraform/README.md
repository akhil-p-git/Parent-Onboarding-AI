# Terraform Infrastructure

This directory contains Terraform configurations for deploying the Zapier Triggers API infrastructure on AWS.

## Architecture

The infrastructure consists of:
- **VPC**: Multi-AZ networking with public, private, and database subnets
- **RDS PostgreSQL**: Managed database with automatic backups and encryption
- **ElastiCache Redis**: In-memory caching with replication
- **SQS**: Message queues for async event processing
- **ECS Fargate**: Serverless container orchestration
- **ALB**: Application Load Balancer with SSL termination

## Directory Structure

```
terraform/
├── bootstrap/          # State backend setup (run first)
├── modules/            # Reusable Terraform modules
│   ├── vpc/           # VPC, subnets, security groups
│   ├── rds/           # PostgreSQL database
│   ├── elasticache/   # Redis cache
│   ├── sqs/           # Message queues
│   ├── ecs/           # ECS cluster and services
│   └── alb/           # Application Load Balancer
├── environments/       # Environment-specific configurations
│   ├── dev/
│   ├── staging/
│   └── production/
├── main.tf            # Root module
├── variables.tf       # Input variables
├── outputs.tf         # Output values
└── versions.tf        # Provider versions
```

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.5.0
3. An SSL certificate in ACM for HTTPS

## Getting Started

### 1. Bootstrap State Backend

First, create the S3 bucket and DynamoDB table for state management:

```bash
cd bootstrap
terraform init
terraform apply
```

### 2. Deploy Environment

```bash
# Navigate to the environment
cd environments/dev

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

## Environment Differences

| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| RDS Instance | db.t3.micro | db.t3.small | db.r6g.large |
| RDS Multi-AZ | No | No | Yes |
| Redis Instance | cache.t3.micro | cache.t3.small | cache.r6g.large |
| Redis Replicas | 0 | 1 | 2 |
| ECS Tasks (API) | 1 | 2 | 3+ |
| NAT Gateways | 1 | 1 | Per AZ |
| VPC Endpoints | No | Yes | Yes |
| Container Insights | No | Yes | Yes |
| Log Retention | 7 days | 14 days | 90 days |

## Useful Commands

```bash
# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Plan changes
terraform plan -out=plan.tfplan

# Apply changes
terraform apply plan.tfplan

# Destroy infrastructure (dev only!)
terraform destroy

# Import existing resource
terraform import aws_s3_bucket.example bucket-name
```

## Secrets Management

Database credentials and Redis auth tokens are automatically generated and stored in AWS Secrets Manager. The ECS tasks are configured to pull these secrets at runtime.

## Monitoring

CloudWatch alarms are configured for:
- RDS: CPU utilization, connection count, storage space
- Redis: CPU utilization, memory usage, replication lag
- SQS: Queue depth, DLQ message count
- ALB: 5XX errors, 4XX errors, response time, unhealthy hosts

## Cost Optimization

Development environment is optimized for cost:
- Single NAT gateway
- No VPC endpoints
- Minimal instance sizes
- No multi-AZ for databases
- Shorter log retention

Production environment is optimized for reliability:
- NAT gateway per AZ
- VPC endpoints for AWS services
- Multi-AZ databases
- Enhanced monitoring
- Longer log retention
