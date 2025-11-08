# Gunicorn Configuration for Django + Cloudinary uploads
# This file should be used to configure Gunicorn for better handling of long-running requests

# gunicorn_config.py
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 600  # 10 minutes for Excel file processing with images
keepalive = 2
graceful_timeout = 300  # 5 minutes for graceful shutdown

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# For file uploads (like Excel files with images)
client_max_body_size = "50M"  # Note: This is actually nginx config, not gunicorn
max_requests_jitter = 50
preload_app = True  # Improve memory usage

# Usage:
# gunicorn --config gunicorn_config.py pneushop.wsgi:application

# OR for Docker:
# CMD ["gunicorn", "--config", "gunicorn_config.py", "pneushop.wsgi:application"]

# Dockerfile updates needed:
# Add to Dockerfile after the Django app setup:
# COPY gunicorn_config.py .
# CMD ["gunicorn", "--config", "gunicorn_config.py", "pneushop.wsgi:application"]