resource "google_dns_managed_zone" "main" {
  name        = local.config.dns.zone_name
  dns_name    = "${local.config.dns.domain_name}."
  project     = local.config.backend.project_id
  description = local.config.dns.description

  dnssec_config {
    state = "on"
  }
}