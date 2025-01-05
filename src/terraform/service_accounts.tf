resource "google_service_account" "gke_nodes" {
  account_id   = "${local.config.cluster.name}-node-sa"
  display_name = "GKE Node Service Account"
}

# IAM bindings for the service account
resource "google_project_iam_member" "node_logging" {
  project = local.config.backend.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_project_iam_member" "node_monitoring" {
  project = local.config.backend.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_project_iam_member" "node_monitoring_viewer" {
  project = local.config.backend.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_project_iam_member" "node_artifact_registry" {
  project = local.config.backend.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}
