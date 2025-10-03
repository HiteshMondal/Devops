# variables.tf - Input variables
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-north-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "devops_project"
  type        = string
  default     = "devops-demo"
}

variable "owner_email" {
  description = "Owner email for tagging"
  type        = string
  default     = "mehiteshmondal@gmail.com"
}

variable "instance_type" {
  description = "EC2 instance type (use t2.micro for free tier)"
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "Name of the SSH key pair"
  type        = string
  default     = "terraform_key"
}

variable "allowed_ssh_ips" {
  description = "List of IPs allowed to SSH"
  type        = list(string)
  default     = ["192.168.0.184/32"] # Change to your IP for security
}