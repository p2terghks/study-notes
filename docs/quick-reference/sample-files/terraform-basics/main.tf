terraform {
  required_version = ">= 1.5, < 2.0"
}

variable "environment" {
  type    = string
  default = "dev"

  validation {
    condition     = contains(["dev", "stg", "prd"], var.environment)
    error_message = "environment must be dev, stg, or prd."
  }
}

locals {
  services = toset(["web", "api"])
}

resource "terraform_data" "service" {
  for_each = local.services
  input    = "${each.key}-${var.environment}"
}

output "service_names" {
  value = { for name, service in terraform_data.service : name => service.output }
}
