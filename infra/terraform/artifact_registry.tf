resource "google_artifact_registry_repository" "modelops" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repo_id
  description   = "ModelOps API images"
  format        = "DOCKER"

  depends_on = [google_project_service.required]
}
