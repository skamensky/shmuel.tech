resource "google_service_account" "gke_nodes" {
  account_id   = "${local.config.cluster.name}-node-sa"
  display_name = "GKE Node Service Account"
}

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

resource "google_service_account" "external_dns" {
  account_id   = "external-dns-admin"
  display_name = "ExternalDNS Service Account"
}

resource "google_project_iam_member" "external_dns_admin" {
  project = local.config.backend.project_id
  role    = "roles/dns.admin"
  member  = "serviceAccount:${google_service_account.external_dns.email}"
}

// service-account key for external-dns:
resource "google_service_account_key" "external_dns" {
  service_account_id = google_service_account.external_dns.name
}

resource "google_service_account" "external_secrets" {
  account_id   = "external-secrets-reader"
  display_name = "External Secrets Service Account"
}

resource "google_project_iam_member" "external_secrets_secret_accessor" {
  project = local.config.backend.project_id
  role    = "roles/secretmanager.viewer"
  member  = "serviceAccount:${google_service_account.external_secrets.email}"
}
