resource "aws_ecr_repository" "app" {
  name                 = var.name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
  lifecycle { prevent_destroy = true }
}
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.name}"
  retention_in_days = 30
}
resource "aws_db_subnet_group" "main" {
  name       = "${var.name}-db"
  subnet_ids = aws_subnet.db[*].id
}
resource "aws_db_instance" "main" {
  identifier                  = "${var.name}-db"
  engine                      = "postgres"
  engine_version              = var.db_engine_version
  instance_class              = "db.t4g.micro"
  db_name                     = "campus"
  username                    = "campus_admin"
  manage_master_user_password = true
  allocated_storage           = 20
  max_allocated_storage       = 100
  storage_type                = "gp3"
  storage_encrypted           = true
  db_subnet_group_name        = aws_db_subnet_group.main.name
  vpc_security_group_ids      = [aws_security_group.db.id]
  publicly_accessible         = false
  multi_az                    = var.db_multi_az
  backup_retention_period     = 7
  deletion_protection         = true
  skip_final_snapshot         = false
  final_snapshot_identifier   = "${var.name}-final"
  auto_minor_version_upgrade  = true
  copy_tags_to_snapshot       = true
  apply_immediately           = false
  lifecycle { prevent_destroy = true }
}
# 비밀정보의 이름만 생성. 실제 값은 나중에 Secrets Manager 콘솔에서 저장한다.
# secret_string이나 비밀번호 data source를 사용하지 않아 실제 값을 state로 읽지 않는다.
resource "aws_secretsmanager_secret" "app" {
  name                    = "${var.name}/database"
  recovery_window_in_days = 30
  lifecycle { prevent_destroy = true }
}
