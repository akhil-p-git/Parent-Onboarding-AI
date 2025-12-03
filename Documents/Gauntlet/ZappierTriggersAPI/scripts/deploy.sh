#!/bin/bash
# Quick deploy script for multi-app infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../infrastructure/terraform/deploy"

echo "🚀 Multi-App Deployment Script"
echo "=============================="
echo ""

# Check AWS credentials
echo "1️⃣  Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured!"
    echo ""
    echo "Run one of these:"
    echo "  aws configure              # For access keys"
    echo "  aws configure sso          # For AWS SSO"
    echo ""
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-east-1")
echo "✅ Logged in to AWS Account: $ACCOUNT_ID (Region: $REGION)"
echo ""

# Check Terraform
echo "2️⃣  Checking Terraform..."
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not installed!"
    echo ""
    echo "Install: https://developer.hashicorp.com/terraform/downloads"
    echo "  macOS: brew install terraform"
    echo "  Linux: sudo snap install terraform --classic"
    exit 1
fi
echo "✅ Terraform version: $(terraform version -json | jq -r '.terraform_version')"
echo ""

# Navigate to terraform directory
cd "$TERRAFORM_DIR"

# Check for tfvars
if [ ! -f "terraform.tfvars" ]; then
    echo "3️⃣  Creating terraform.tfvars from example..."
    cp terraform.tfvars.example terraform.tfvars
    echo "⚠️  Please edit terraform.tfvars with your settings!"
    echo "    File location: $TERRAFORM_DIR/terraform.tfvars"
    echo ""
    echo "Then run this script again."
    exit 0
fi

echo "3️⃣  Initializing Terraform..."
terraform init

echo ""
echo "4️⃣  Planning infrastructure..."
terraform plan -out=tfplan

echo ""
echo "=============================="
echo "📋 Review the plan above"
echo ""
read -p "5️⃣  Deploy infrastructure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo ""
    echo "🚀 Deploying..."
    terraform apply tfplan

    echo ""
    echo "=============================="
    echo "✅ Deployment complete!"
    echo ""
    echo "📍 Important outputs:"
    terraform output

    echo ""
    echo "📝 Next steps:"
    echo "  1. Point your domain DNS to the ALB DNS name above"
    echo "  2. Build and push Docker images to ECR repositories"
    echo "  3. ECS will automatically deploy once images are available"
    echo ""
    echo "To push a Docker image:"
    echo "  aws ecr get-login-password | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
    echo "  docker build -t your-app ."
    echo "  docker tag your-app:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/dev/your-app:latest"
    echo "  docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/dev/your-app:latest"
else
    echo "Cancelled."
    rm -f tfplan
fi
