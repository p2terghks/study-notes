variable "region" {
  type    = string
  default = "ap-northeast-2"
}
variable "name" {
  type    = string
  default = "campus-tf"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,19}$", var.name))
    error_message = "Use 3-20 lowercase letters, numbers, hyphens; start with a letter."
  }
}
variable "domain" {
  type        = string
  description = "Owned hostname, e.g. campus.your-domain.com."
}
variable "zone_id" {
  type        = string
  description = "Existing authoritative PUBLIC Route 53 hosted zone ID in this account."
}
variable "db_engine_version" {
  type        = string
  description = "Exact PostgreSQL version available with db.t4g.micro in the selected region."
}
variable "db_multi_az" {
  type    = bool
  default = true
}
variable "app_enabled" {
  type    = bool
  default = false
}
variable "image_uri" {
  type    = string
  default = ""
}
variable "desired_count" {
  type    = number
  default = 2
  validation {
    condition     = var.desired_count >= 1 && floor(var.desired_count) == var.desired_count
    error_message = "desired_count must be a positive integer."
  }
}
