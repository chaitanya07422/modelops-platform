locals {
  model_bucket = var.model_bucket_name != "" ? var.model_bucket_name : "${var.project_id}-models"
}

resource "google_storage_bucket" "models" {
  name                        = local.model_bucket
  project                     = var.project_id
  location                    = upper(var.region)
  force_destroy               = false
  uniform_bucket_level_access = true

  # Keep objects if the bucket resource is removed from state/accidentally destroyed
  # only when force_destroy is true; default false protects demo models.

  depends_on = [google_project_service.required]
}
