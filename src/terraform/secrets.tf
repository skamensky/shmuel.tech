resource "google_secret_manager_secret" "external_dns_key" {
  secret_id = "external-dns-key"
  replication {
    user_managed {
      replicas {
        location = local.config.cluster.region
      }
    }
  }
}

resource "google_secret_manager_secret_version" "external_dns_key_version" {
  secret = google_secret_manager_secret.external_dns_key.id
  secret_data = google_service_account_key.external_dns.private_key
}
