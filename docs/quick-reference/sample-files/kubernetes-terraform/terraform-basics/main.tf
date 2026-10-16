terraform {
  required_version = ">= 1.4, < 2.0"
}

variable "environment" {
  description = "학습 환경 이름"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "environment는 dev, stage, prod 중 하나여야 합니다."
  }
}

variable "replicas" {
  description = "앱 복제본 목표를 표현하는 학습용 숫자"
  type        = number
  default     = 2

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 5 && floor(var.replicas) == var.replicas
    error_message = "replicas는 1부터 5 사이의 정수여야 합니다."
  }
}

locals {
  app_name = "lecture-${var.environment}"
}

resource "terraform_data" "lesson" {
  input = {
    name     = local.app_name
    replicas = var.replicas
  }
}

output "lesson" {
  description = "state에 기록된 학습용 결과. 실제 서버나 Pod는 만들지 않습니다."
  value       = terraform_data.lesson.output
}
