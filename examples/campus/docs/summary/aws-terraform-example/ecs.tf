data "aws_partition" "current" {}
data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}
resource "aws_iam_role" "execution" {
  name               = "${var.name}-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}
resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
resource "aws_iam_role_policy" "secret" {
  name = "read-app-secret"
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = aws_secretsmanager_secret.app.arn
    }]
  })
}
resource "aws_iam_role" "task" {
  name               = "${var.name}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}
resource "aws_ecs_cluster" "main" { name = var.name }
resource "aws_ecs_task_definition" "app" {
  count                    = var.app_enabled ? 1 : 0
  family                   = var.name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }
  container_definitions = jsonencode([{
    name         = "campus"
    image        = var.image_uri
    essential    = true
    user         = "10001:10001"
    stopTimeout  = 60
    portMappings = [{ containerPort = 8080, protocol = "tcp" }]
    environment = [
      { name = "SPRING_PROFILES_ACTIVE", value = "prod" },
      { name = "DB_POOL_SIZE", value = "10" },
      {
        name  = "DB_URL"
        value = "jdbc:postgresql://${aws_db_instance.main.address}:5432/campus?sslmode=verify-full&sslrootcert=/app/certs/global-bundle.pem"
      }
    ]
    secrets = [
      { name = "DB_USERNAME", valueFrom = "${aws_secretsmanager_secret.app.arn}:username::" },
      { name = "DB_PASSWORD", valueFrom = "${aws_secretsmanager_secret.app.arn}:password::" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.app.name
        awslogs-region        = var.region
        awslogs-stream-prefix = "campus"
      }
    }
  }])
  lifecycle {
    precondition {
      condition     = startswith(var.image_uri, "${aws_ecr_repository.app.repository_url}@sha256:")
      error_message = "Enable the app only after pushing its ECR image; use its sha256 digest URI."
    }
  }
}
resource "aws_ecs_service" "app" {
  count                              = var.app_enabled ? 1 : 0
  name                               = "${var.name}-service"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.app[0].arn
  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  desired_count                      = var.desired_count
  health_check_grace_period_seconds  = 180
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  wait_for_steady_state              = true
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = aws_subnet.app[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "campus"
    container_port   = 8080
  }
  depends_on = [
    aws_lb_listener.https,
    aws_route_table_association.app,
    aws_iam_role_policy_attachment.execution,
    aws_iam_role_policy.secret,
    aws_vpc_security_group_ingress_rule.app_alb,
    aws_vpc_security_group_ingress_rule.db_app,
    aws_vpc_security_group_egress_rule.app_https,
    aws_vpc_security_group_egress_rule.app_db
  ]
}
