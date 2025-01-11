resource "google_compute_network" "vpc" {
  name                    = "${local.config.cluster.name}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_router" "router" {
  name    = "${local.config.cluster.name}-router"
  network = google_compute_network.vpc.name
  region  = local.config.cluster.region
}

resource "google_compute_router_nat" "nat_gateway" {
  name            = "${local.config.cluster.name}-nat"
  router          = google_compute_router.router.name
  region          = local.config.cluster.region
  nat_ip_allocate_option = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# resource "google_compute_subnetwork" "secondary_subnet" {
#   name          = "${local.config.cluster.name}-secondary-subnet"
#   ip_cidr_range = local.config.cluster.secondary_subnets_cidr
#   network       = google_compute_network.vpc.name
#   region        = local.config.cluster.region

#   secondary_ip_range {
#     range_name    = "pod-ranges"
#     ip_cidr_range = local.config.cluster.pod_cidr
#   }

#   secondary_ip_range {
#     range_name    = "service-ranges"
#     ip_cidr_range = local.config.cluster.service_cidr
#   }
# }

resource "google_compute_subnetwork" "cluster_subnet" {
  name          = "${local.config.cluster.name}-cluster-subnet"
  ip_cidr_range = local.config.cluster.cluster_subnet_cidr
  network       = google_compute_network.vpc.name
  region        = local.config.cluster.region
}

resource "google_compute_firewall" "default_egress" {
  name    = "${local.config.cluster.name}-default-egress"
  network = google_compute_network.vpc.name

  direction = "EGRESS"
  allow {
    protocol = "all"
  }

  destination_ranges = ["0.0.0.0/0"]
  priority           = 65535
  description        = "Default egress rule to allow all outbound traffic"
}


resource "google_compute_firewall" "allow_http_https" {
  name    = "allow-http-https-ingress"
  network = google_compute_network.vpc.name

  direction = "INGRESS"
  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gke-cluster"]
  description   = "Allow HTTP and HTTPS traffic to GKE cluster"
}

# https://cloud.google.com/iap/docs/using-tcp-forwarding#firewall
# for IAP TCP forwarding (i.e. sshing in from the console)
resource "google_compute_firewall" "iap_ssh" {
  name    = "${local.config.cluster.name}-iap-ssh"
  network = google_compute_network.vpc.name

  direction = "INGRESS"
  allow {
    protocol = "all"
  }

  source_ranges = ["35.235.240.0/20"]
  priority      = 1000
  description   = "Allow IAP SSH access"
}

