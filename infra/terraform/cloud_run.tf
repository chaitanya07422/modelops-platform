locals {
  default_image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_id}/modelops-api:latest"
  cloud_run_image = var.cloud_run_image != "" ? var.cloud_run_image : local.default_image
}

resource "google_cloud_run_v2_service" "api" {
  name     = var.cloud_run_service
  project  = var.project_id
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  scaling {
    min_instance_count = var.min_instances
  }

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    timeout                          = "60s"
    max_instance_request_concurrency = 40
    service_account                  = "${data.google_project.current.number}-compute@developer.gserviceaccount.com"

    containers {
      image = local.cloud_run_image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "MODELOPS_ENV"
        value = "production"
      }
      env {
        name  = "MODELOPS_LOG_LEVEL"
        value = "INFO"
      }
      env {
        name  = "MODELOPS_APPROVED_MODEL_PATH"
        value = "/models/approved/model.joblib"
      }
      env {
        name  = "MODELOPS_MODEL_PATH"
        value = "/models/approved/model.joblib"
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  # GitHub CD updates the image / client annotations on every deploy.
  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].image,
      template[0].labels,
      template[0].annotations,
    ]
  }

  depends_on = [
    google_project_service.required,
    google_artifact_registry_repository.modelops,
  ]
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
