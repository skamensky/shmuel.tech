provider "kubernetes" {
  config_path = pathexpand("~/.kube/config")
  config_context = "gke_${local.config.backend.project_id}_${local.config.cluster.location}_${local.config.cluster.name}"
}



provider "helm" {
  kubernetes {
    config_path = pathexpand("~/.kube/config")
    config_context = "gke_${local.config.backend.project_id}_${local.config.cluster.location}_${local.config.cluster.name}"
  }
}

## Secrets ##

resource "kubernetes_namespace" "external_secrets" {
  metadata {
    name = "external-secrets"
  }
}

resource "kubernetes_service_account" "external_secrets" {
  metadata {
    name      = "external-secrets"
    namespace =  kubernetes_namespace.external_secrets.metadata[0].name
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.external_secrets.email
    }
  }
}

resource "google_service_account_iam_member" "external_secrets_workload_identity_binding" {
  service_account_id = google_service_account.external_secrets.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${local.config.backend.project_id}.svc.id.goog[external-secrets/external-secrets]"
}

resource "helm_release" "external_secrets" {
  name       = "external-secrets"
  namespace  = kubernetes_namespace.external_secrets.metadata[0].name
  chart      = "external-secrets"
  repository = "https://charts.external-secrets.io"
  version    = "0.8.0" 

  set {
    name  = "serviceAccount.create"
    value = "false"
  }

  set {
    name  = "serviceAccount.name"
    value = kubernetes_service_account.external_secrets.metadata[0].name
  }

  set {
    name  = "google.projectId"
    value = local.config.backend.project_id
  }

  set {
    name  = "syncWatchNamespace"
    value = "default"
  }

  depends_on = [
    kubernetes_namespace.external_secrets,
    kubernetes_service_account.external_secrets,
    google_service_account_iam_member.external_secrets_workload_identity_binding
  ]
}




## DNS ##

resource "kubernetes_service_account" "external_dns" {
  metadata {
    name      = "external-dns"
    namespace = "default" # Replace with your desired namespace
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.external_dns.email
    }
  }
}

resource "google_service_account_iam_member" "external_dns_workload_identity_binding" {
  service_account_id = google_service_account.external_dns.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${local.config.backend.project_id}.svc.id.goog[default/external-dns]"
}

resource "kubernetes_namespace" "external_dns" {
  metadata {
    name = "external-dns"
  }
}

resource "helm_release" "external_dns" {
  name       = "external-dns"
  namespace  =  kubernetes_namespace.external_dns.metadata[0].name
  chart      = "external-dns"
  repository =  "oci://registry-1.docker.io/bitnamicharts"
  version    = "8.7.1"

  set {
    name  = "domainFilters[0]"
    value = local.config.dns.domain_name
  }

  set {
    name  = "provider"
    value = "google"
  }

  set {
    name  = "google.project"
    value = local.config.backend.project_id
  }

  set {
    name  = "serviceAccount.name"
    value = kubernetes_service_account.external_dns.metadata[0].name
  }

  set {
    name  = "policy"
    value = "upsert-only"
  }

  set {
    name  = "registry"
    value = "txt"
  }

  set {
    name  = "txtOwnerId"
    value = "external-dns"
  }

  depends_on = [
    kubernetes_service_account.external_dns,
    google_service_account_iam_member.external_dns_workload_identity_binding,
    kubernetes_namespace.external_dns
  ]
}
