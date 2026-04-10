output "vpc_id" {
  value = module.vpc.vpc_id
}

output "api_service_url" {
  value = module.ecs.api_service_url
}

output "rds_endpoint" {
  value     = module.rds.endpoint
  sensitive = true
}

output "s3_bucket" {
  value = module.s3.bucket_name
}
