# platform/infra/OpenTofu/cloudsql.tf
# Cloud SQL (PostgreSQL). Unlike GKE/Compute Engine, Cloud SQL has NO
# permanent Always-Free tier — every instance bills. It's gated behind
# enable_cloudsql (default false, .env → not set = off) so `tofu apply`
# never charges you for a database unless you explicitly opt in.

resource "google_sql_database_instance" "primary" {
  count = var.enable_cloudsql ? 1 : 0

  provider = google

  name             = "${var.app_name}-db"
  region           = var.gcp_region
  database_version = var.cloudsql_version

  settings {
    tier              = var.cloudsql_tier
    availability_type = "ZONAL"
    disk_size         = var.cloudsql_disk_size_gb
    disk_type         = "PD_HDD"
    disk_autoresize   = false

    backup_configuration {
      enabled = false
    }

    ip_configuration {
      ipv4_enabled = true
    }

    user_labels = local.common_labels
  }

  deletion_protection = false

  depends_on = [google_project_service.required]
}

resource "google_sql_database" "app_db" {
  count = var.enable_cloudsql ? 1 : 0

  name     = var.db_name
  instance = google_sql_database_instance.primary[0].name
}

resource "google_sql_user" "app_user" {
  count = var.enable_cloudsql ? 1 : 0

  name     = var.db_username
  instance = google_sql_database_instance.primary[0].name
  password = var.db_password
}
