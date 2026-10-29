variable "project_id" {
  type        = string
  description = "GCP project id (bring-your-own)."
}

variable "region" {
  type        = string
  description = "Primary region for Artifact Registry, Cloud Run, and the models bucket."
  default     = "us-central1"
}

variable "artifact_repo_id" {
  type        = string
  description = "Artifact Registry repository id."
  default     = "modelops"
}

variable "model_bucket_name" {
  type        = string
  description = "GCS bucket for approved model artifacts (CD downloads from here)."
  default     = ""
}

variable "cloud_run_service" {
  type        = string
  description = "Cloud Run service name."
  default     = "modelops-api"
}

variable "cloud_run_image" {
  type        = string
  description = "Container image for Cloud Run. CD updates this; Terraform ignores image drift after apply."
  default     = ""
}

variable "deploy_sa_id" {
  type        = string
  description = "GitHub Actions deploy service account id (without domain)."
  default     = "modelops-github-deploy"
}

variable "min_instances" {
  type        = number
  description = "Cloud Run min instances (0 = scale to zero)."
  default     = 0
}

variable "max_instances" {
  type        = number
  description = "Cloud Run max instances."
  default     = 2
}

variable "cpu" {
  type        = string
  description = "Cloud Run CPU limit."
  default     = "1"
}

variable "memory" {
  type        = string
  description = "Cloud Run memory limit."
  default     = "512Mi"
}
