terraform {
  required_version = "= 1.5.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
  backend "gcs" {
    bucket = "kelev"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = local.config.backend.project_id
  region  = local.config.backend.tf_region
}

provider "google-beta" {
  project = local.config.backend.project_id
  region  = local.config.backend.tf_region
}
