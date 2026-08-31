# platform/infra/OpenTofu/gke.tf
# GKE cluster sized for GCP's Always-Free tier.
#
# Always-Free covers (per billing account):
#   - the cluster-management fee for one zonal (non-Autopilot) cluster
#   - e2-micro Compute Engine usage, in us-west1 / us-central1 / us-east1 only
#   - 30 GB-months of standard persistent disk
#
# This module provisions a STANDARD zonal cluster (zonal, not regional —
# regional clusters run 3 control-plane replicas and are not covered by
# the fee waiver) with its default node pool removed, so node sizing is
# fully controlled by gke_machine_type / gke_node_count / gke_disk_size_gb.

resource "google_container_cluster" "primary" {
  provider = google

  name     = var.gke_cluster_name
  location = var.gcp_zone # zonal — required for the free cluster-management-fee waiver

  remove_default_node_pool = true
  initial_node_count       = 1

  release_channel {
    channel = var.gke_release_channel
  }

  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {}

  workload_identity_config {
    workload_pool = "${var.gcp_project_id}.svc.id.goog"
  }

  # This module treats the cluster as fully disposable/reproducible from
  # code, matching the AWS (EKS) and Azure (AKS) modules in this repo.
  deletion_protection = false

  depends_on = [google_project_service.required]
}

resource "google_container_node_pool" "primary_nodes" {
  provider = google

  name     = "${var.gke_cluster_name}-pool"
  cluster  = google_container_cluster.primary.name
  location = var.gcp_zone

  node_count = var.gke_node_count

  node_config {
    machine_type = var.gke_machine_type
    disk_size_gb = var.gke_disk_size_gb
    disk_type    = "pd-standard"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = local.common_labels
    tags   = [var.app_name]
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}
