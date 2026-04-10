variable "project" {
  default = "sbu-assistant"
}

variable "environment" {
  default = "production"
}

variable "aws_region" {
  default = "us-east-1"
}

variable "db_username" {
  default   = "sbu_user"
  sensitive = true
}

variable "db_password" {
  sensitive = true
}

variable "redis_url" {
  default = "redis://redis:6379/0"
}
