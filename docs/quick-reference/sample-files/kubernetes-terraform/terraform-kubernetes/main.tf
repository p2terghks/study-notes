terraform {
  required_version = ">= 1.4, < 2.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.38.0"
    }
  }
}

variable "kubeconfig_path" {
  description = "로컬 kind 클러스터 전용 kubeconfig 경로"
  type        = string
  default     = "~/.kube/lecture-kind.yaml"
}

variable "replicas" {
  description = "실습 Deployment 복제본 수"
  type        = number
  default     = 2

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 5 && floor(var.replicas) == var.replicas
    error_message = "replicas는 1부터 5 사이의 정수여야 합니다."
  }
}

provider "kubernetes" {
  config_path    = pathexpand(var.kubeconfig_path)
  config_context = "kind-lecture-local"
}

resource "kubernetes_namespace_v1" "lecture" {
  metadata {
    name = "lecture-tf"
  }
}

resource "kubernetes_deployment_v1" "web" {
  metadata {
    name      = "lecture-web"
    namespace = kubernetes_namespace_v1.lecture.metadata[0].name
  }

  spec {
    replicas = var.replicas
    selector {
      match_labels = { app = "lecture-tf-web" }
    }
    template {
      metadata {
        labels = { app = "lecture-tf-web" }
      }
      spec {
        container {
          name  = "nginx"
          image = "nginx:1.28.0-alpine"
          port {
            name           = "http"
            container_port = 80
          }
          resources {
            requests = { cpu = "100m", memory = "32Mi" }
            limits   = { cpu = "500m", memory = "128Mi" }
          }
          readiness_probe {
            http_get {
              path = "/"
              port = 80
            }
            period_seconds = 5
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "web" {
  metadata {
    name      = "lecture-web"
    namespace = kubernetes_namespace_v1.lecture.metadata[0].name
  }
  spec {
    selector = { app = "lecture-tf-web" }
    port {
      port        = 80
      target_port = 80
    }
    type = "ClusterIP"
  }
}

output "namespace" {
  value = kubernetes_namespace_v1.lecture.metadata[0].name
}
