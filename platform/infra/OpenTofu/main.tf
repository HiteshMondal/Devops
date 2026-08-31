# platform/infra/OpenTofu/main.tf
# Enables the GCP APIs this module depends on so it works on a brand-new
# project with zero manual `gcloud services enable` steps. Re-applying is
# always safe — enabling an already-enabled API is a no-op.

locals {
  required_apis = [
    "compute.googleapis.com",
    "container.googleapis.com",
    "sqladmin.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
  ]

  common_labels = {
    app         = var.app_name
    environment = var.deploy_target
    managed_by  = "opentofu"
  }
}

resource "google_project_service" "required" {
  for_each = toset(local.required_apis)

  project            = var.gcp_project_id
  service            = each.value
  disable_on_destroy = false
}
