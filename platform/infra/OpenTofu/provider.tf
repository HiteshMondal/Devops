# platform/infra/OpenTofu/provider.tf
# GCP Provider Configuration — OpenTofu
#
# Authentication:
#   Uses Application Default Credentials (ADC) by default — nothing is
#   hardcoded, so this works identically on any machine. Either:
#     gcloud auth application-default login
#   or export GOOGLE_APPLICATION_CREDENTIALS to a service-account JSON key
#   (see .env → GOOGLE_APPLICATION_CREDENTIALS).

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  # Local state by default so this module runs out-of-the-box on any
  # machine with zero setup. For team/shared use, swap this for a GCS
  # backend (the bucket must already exist — OpenTofu cannot create its
  # own backend):
  #
  # backend "gcs" {
  #   bucket = "REPLACE_WITH_YOUR_STATE_BUCKET"
  #   prefix = "devops-platform/opentofu"
  # }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}
