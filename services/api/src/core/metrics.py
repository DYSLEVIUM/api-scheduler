import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response


http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000)
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint", "status_code"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000)
)

active_schedules = Gauge(
    "active_schedules_total",
    "Total number of active schedules"
)

active_jobs = Gauge(
    "active_jobs_total",
    "Total number of active jobs"
)

schedule_executions_total = Counter(
    "schedule_executions_total",
    "Total number of schedule executions",
    ["schedule_id", "status"]
)

job_duration_seconds = Histogram(
    "job_duration_seconds",
    "Job execution duration in seconds",
    ["schedule_id", "status"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

process_cpu_percent = Gauge(
    "process_cpu_percent",
    "Process CPU usage percentage"
)

process_memory_bytes = Gauge(
    "process_memory_bytes",
    "Process memory usage in bytes"
)

process_threads = Gauge(
    "process_threads",
    "Number of threads used by the process"
)

system_cpu_percent = Gauge(
    "system_cpu_percent",
    "System-wide CPU usage percentage"
)

system_memory_percent = Gauge(
    "system_memory_percent",
    "System-wide memory usage percentage"
)

system_memory_available_bytes = Gauge(
    "system_memory_available_bytes",
    "System available memory in bytes"
)


def update_system_metrics():
    process = psutil.Process()
    
    process_cpu_percent.set(process.cpu_percent())
    
    mem_info = process.memory_info()
    process_memory_bytes.set(mem_info.rss)
    
    process_threads.set(process.num_threads())
    
    system_cpu_percent.set(psutil.cpu_percent(interval=0))
    
    system_mem = psutil.virtual_memory()
    system_memory_percent.set(system_mem.percent)
    system_memory_available_bytes.set(system_mem.available)


def get_metrics_response() -> Response:
    update_system_metrics()
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
