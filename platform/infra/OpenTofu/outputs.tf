# platform/infra/OpenTofu/outputs.tf

output "gke_cluster_name" {
  description = "GKE cluster name."
  value       = google_container_cluster.primary.name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster API endpoint."
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "gke_get_credentials_command" {
  description = "Run this to point kubectl at the new cluster."
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --zone ${var.gcp_zone} --project ${var.gcp_project_id}"
}

output "cloudsql_connection_name" {
  description = "Cloud SQL instance connection name. Null when enable_cloudsql=false."
  value       = var.enable_cloudsql ? google_sql_database_instance.primary[0].connection_name : null
}

output "cloudsql_public_ip" {
  description = "Cloud SQL public IP address. Null when enable_cloudsql=false."
  value       = var.enable_cloudsql ? google_sql_database_instance.primary[0].public_ip_address : null
  sensitive   = true
}
