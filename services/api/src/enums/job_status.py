from enum import Enum


class JobStatus(str, Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    DNS_ERROR = "dns_error"
    CONNECTION_ERROR = "connection_error"
    HTTP_4XX = "http_4xx"
    HTTP_5XX = "http_5xx"
    ERROR = "error"
