variable "project" {}
variable "environment" {}
variable "vpc_id" {}
variable "private_subnet_ids" { type = list(string) }
variable "db_username" {}
variable "db_password" {}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-${var.environment}-db-subnet"
  subnet_ids = var.private_subnet_ids
}

resource "aws_security_group" "rds" {
  name   = "${var.project}-${var.environment}-rds-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_db_instance" "main" {
  identifier             = "${var.project}-${var.environment}"
  engine                 = "postgres"
  engine_version         = "16.4"
  instance_class         = "db.t3.medium"
  allocated_storage      = 50
  max_allocated_storage  = 200
  db_name                = "sbu_assistant"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true
  backup_retention_period = 7
  multi_az               = false

  tags = { Name = "${var.project}-${var.environment}-rds" }
}

output "endpoint" { value = aws_db_instance.main.endpoint }
output "connection_string" {
  value     = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/sbu_assistant"
  sensitive = true
}
