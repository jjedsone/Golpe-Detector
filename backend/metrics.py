"""
Sistema de métricas e monitoramento
"""
import time
from functools import wraps
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Métricas em memória (em produção, usar Redis ou Prometheus)
metrics = {
    "requests_total": 0,
    "requests_by_endpoint": {},
    "requests_by_status": {},
    "processing_times": [],
    "errors": [],
    "worker_jobs_processed": 0,
    "worker_jobs_failed": 0,
}

def record_metric(name, value=1, labels=None):
    """Registra uma métrica"""
    if name not in metrics:
        if labels:
            metrics[name] = {}
        else:
            metrics[name] = 0
    
    if isinstance(metrics[name], dict):
        # Métricas com labels
        label_key = str(labels) if labels else "default"
        if label_key not in metrics[name]:
            metrics[name][label_key] = 0
        metrics[name][label_key] += value
    elif isinstance(metrics[name], (int, float)):
        metrics[name] += value
    elif isinstance(metrics[name], list):
        metrics[name].append({
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "labels": labels or {}
        })
        # Manter apenas últimas 1000 entradas
        if len(metrics[name]) > 1000:
            metrics[name] = metrics[name][-1000:]

def get_metrics():
    """Retorna todas as métricas"""
    return {
        **metrics,
        "avg_processing_time": (
            sum(metrics["processing_times"]) / len(metrics["processing_times"])
            if metrics["processing_times"] else 0
        ),
        "error_rate": (
            len(metrics["errors"]) / metrics["requests_total"]
            if metrics["requests_total"] > 0 else 0
        )
    }

def reset_metrics():
    """Reseta todas as métricas"""
    global metrics
    metrics = {
        "requests_total": 0,
        "requests_by_endpoint": {},
        "requests_by_status": {},
        "processing_times": [],
        "errors": [],
        "worker_jobs_processed": 0,
        "worker_jobs_failed": 0,
    }

def track_request(endpoint, status_code, processing_time):
    """Registra uma requisição"""
    record_metric("requests_total")
    record_metric("requests_by_endpoint", labels={"endpoint": endpoint})
    record_metric("requests_by_status", labels={"status": status_code})
    record_metric("processing_times", value=processing_time)
    
    if status_code >= 400:
        record_metric("errors", labels={"endpoint": endpoint, "status": status_code})

def track_worker_job(success=True):
    """Registra processamento de job do worker"""
    if success:
        record_metric("worker_jobs_processed")
    else:
        record_metric("worker_jobs_failed")

