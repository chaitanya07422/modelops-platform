output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.modelops.name
}

output "model_bucket" {
  value = google_storage_bucket.models.name
}

output "cloud_run_uri" {
  value = google_cloud_run_v2_service.api.uri
}

output "deploy_service_account_email" {
  value = google_service_account.github_deploy.email
}
