terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Local state for the portfolio sandbox. Prefer a GCS backend before team use.
  # backend "gcs" {
  #   bucket = "modelops-platform-tfstate"
  #   prefix = "infra"
  # }
}
