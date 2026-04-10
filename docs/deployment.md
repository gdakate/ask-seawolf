# Deployment Guide

## AWS Architecture

The platform is designed for deployment on AWS using:
- **ECS/Fargate** for the API and worker containers
- **RDS PostgreSQL** for the database (with pgvector extension)
- **S3** for document storage
- **ALB** for API load balancing
- **Amplify Hosting** for frontend apps
- **CloudWatch** for logging and monitoring

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.5
- Docker for building container images
- An ECR repository for container images

## Infrastructure Setup

```bash
cd infra/terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan -var="db_password=YOUR_SECURE_PASSWORD"

# Apply infrastructure
terraform apply -var="db_password=YOUR_SECURE_PASSWORD"
```

This creates: VPC, subnets, RDS instance, S3 bucket, ECS cluster, ALB, IAM roles, and CloudWatch log groups.

## Container Deployment

```bash
# Build and push API image
cd apps/api
docker build -t sbu-assistant-api .
docker tag sbu-assistant-api:latest <ECR_URI>/sbu-assistant-api:latest
docker push <ECR_URI>/sbu-assistant-api:latest

# Update ECS service
aws ecs update-service --cluster sbu-assistant-production --service sbu-assistant-production-api --force-new-deployment
```

## Frontend Deployment

Both frontend apps are structured for Amplify Hosting:

```bash
# In the Amplify console or CLI:
# 1. Connect the repository
# 2. Set build settings for apps/web or apps/admin
# 3. Set environment variable: NEXT_PUBLIC_API_URL=<ALB_URL>
# 4. Deploy
```

## Environment Variables (Production)

Set these in ECS task definitions or AWS Secrets Manager:

```
AI_PROVIDER=openai  # or bedrock
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://user:pass@rds-endpoint:5432/sbu_assistant
REDIS_URL=redis://elasticache-endpoint:6379/0
JWT_SECRET=<generate-a-long-random-string>
STORAGE_BACKEND=s3
S3_BUCKET=sbu-assistant-production-docs
ENVIRONMENT=production
CORS_ORIGINS=https://your-domain.com
```

## Database Setup

After RDS is provisioned:

```bash
# Run migrations
docker run --rm -e DATABASE_URL_SYNC=<RDS_URL> sbu-assistant-api alembic upgrade head

# Enable pgvector extension (done automatically by migration)
# Seed initial data if needed
docker run --rm -e DATABASE_URL=<RDS_URL> sbu-assistant-api python -m seed.seed_data
```

## Health Checks

The API exposes `GET /api/health` which returns service status. The ALB target group is configured to use this endpoint.

## Monitoring

- **CloudWatch Logs**: All container output is streamed to CloudWatch log groups
- **ALB Metrics**: Request count, latency, error rates available in CloudWatch
- **RDS Metrics**: CPU, connections, storage available in RDS console
