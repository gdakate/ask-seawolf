terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "sbu-assistant-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source     = "./modules/vpc"
  project    = var.project
  environment = var.environment
}

module "rds" {
  source            = "./modules/rds"
  project           = var.project
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  db_username       = var.db_username
  db_password       = var.db_password
}

module "s3" {
  source      = "./modules/s3"
  project     = var.project
  environment = var.environment
}

module "iam" {
  source      = "./modules/iam"
  project     = var.project
  environment = var.environment
  s3_bucket_arn = module.s3.bucket_arn
}

module "ecs" {
  source             = "./modules/ecs"
  project            = var.project
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  execution_role_arn = module.iam.ecs_execution_role_arn
  task_role_arn      = module.iam.ecs_task_role_arn
  database_url       = module.rds.connection_string
  redis_url          = var.redis_url
}
