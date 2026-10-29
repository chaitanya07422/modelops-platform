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

output "monitoring_dashboard_id" {
  value       = google_monitoring_dashboard.modelops_api.id
  description = "Cloud Monitoring dashboard for Cloud Run request/latency/CPU charts"
}

output "monitoring_console_url" {
  value = "https://console.cloud.google.com/monitoring/dashboards?project=${var.project_id}"
}

output "cloud_run_metrics_console_url" {
  value = "https://console.cloud.google.com/run/detail/${var.region}/${var.cloud_run_service}/metrics?project=${var.project_id}"
}

output "prometheus_text_url" {
  value       = "${google_cloud_run_v2_service.api.uri}/metrics"
  description = "App-exported Prometheus text (modelops_*). Not scraped into GCP unless a collector is added."
}
