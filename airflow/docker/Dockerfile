# RealMap Airflow Custom Image
# Extends official Airflow image with project dependencies

FROM apache/airflow:2.10.4

# Install project dependencies
# These are required for backend modules to work inside Airflow tasks
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies from requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Note: The realmap codebase is mounted at /opt/realmap via docker-compose volumes
# PYTHONPATH is set to /opt/realmap via docker-compose environment
