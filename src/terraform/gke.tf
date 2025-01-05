resource "google_container_cluster" "primary" {
  name     = local.config.cluster.name
  location = local.config.cluster.location

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.cluster_subnet.name

  workload_identity_config {
    workload_pool = "${local.config.backend.project_id}.svc.id.goog"
  }

  ip_allocation_policy {
    cluster_ipv4_cidr_block  = local.config.cluster.pod_cidr
    services_ipv4_cidr_block = local.config.cluster.service_cidr
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block = local.config.cluster.master_cidr
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "all"
    }
  }
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "${local.config.cluster.name}-node-pool"
  location   = local.config.cluster.location
  cluster    = google_container_cluster.primary.name
  node_count = local.config.cluster.initial_node_count

  
  node_config {
    service_account = google_service_account.gke_nodes.email

    labels = {
      env = local.config.cluster.environment
    }

    machine_type = local.config.cluster.machine_type
    disk_size_gb = local.config.cluster.disk_size_gb
    disk_type    = local.config.cluster.disk_type

    metadata = {
      disable-legacy-endpoints = "true"
    }

    # only putting here so TF doesn't try to update, bug in the provider
    kubelet_config {
      cpu_manager_policy = "static"
       # TODO, revisit this to see if we should change to false.
       # it allows the pods to use more than their cpu quota if there is spare capacity
      cpu_cfs_quota = false
      pod_pids_limit = 0
    }
  }
}
