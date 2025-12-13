# 🔮 Future Architecture & Orchestration Designs

Currently, RealMap uses a custom synchronous Python orchestrator (`runs/orchestrator.py`). As the project scales, moving to a dedicated workflow engine is recommended to handle parallelism, retries, and observability.

## 🏆 Recommendation: Apache Airflow

**Why?**
*   **Postgres Integration**: Native operators for the existing DB.
*   **Human-in-the-loop**: `ExternalTaskSensor` can handle the CAPTCHA wait times.
*   **Observability**: Best-in-class UI for debugging pipeline failures.

### Proposed Airflow DAG

```python
with DAG('realmap_etl', schedule_interval='@daily') as dag:
    
    # 1. Initialization
    init = PythonOperator(task_id='init_browser', ...)
    
    # 2. Acquisition (Wait for CAPTCHA)
    scrape = PythonOperator(task_id='scrape_listings', ...)
    
    # 3. Parallel Processing
    fetch_details = PythonOperator(task_id='fetch_details', ...)
    
    # 4. ETL
    extract = PythonOperator(task_id='extract_raw', ...)
    load = PythonOperator(task_id='load_to_db', ...)
    
    # 5. Fan-out Enrichment
    geocode = PythonOperator(task_id='geocode', ...)
    amenities = PythonOperator(task_id='amenities', ...)
    
    # 6. Scoring
    score = PythonOperator(task_id='compute_scores', ...)

    init >> scrape >> fetch_details >> extract >> load
    load >> [geocode, amenities] >> score
```

## 🥈 Alternative: Prefect

If a purely Pythonic, less infra-heavy approach is preferred, **Prefect** is the strong second choice.

### Proposed Prefect Flow

```python
@flow(name="realmap-flow")
def main_flow():
    config = load_config()
    listings = scrape_listings(config)
    
    # Native mapping for parallelism
    details = fetch_details.map(listings)
    v1_data = extract_and_map.map(details)
    
    load_to_db(v1_data)
    
    # Post-processing triggers
    trigger_enrichment(wait_for=[load_to_db])
```

## 🛑 Current Gaps vs. Future State

| Feature | Current Custom Orchestrator | Airflow/Prefect Future |
|---------|-----------------------------|------------------------|
| **Parallelism** | ❌ Serial execution | ✅ Native parallel task mapping |
| **Retries** | ⚠️ Limited try/except blocks | ✅ Configurable backoff policies |
| **Resume** | ❌ Must restart from scratch | ✅ Resume from failed step |
| **History** | ⚠️ Logs only | ✅ Persistent run history database |
| **Scheduling** | ❌ Cron/Manual | ✅ Built-in scheduler |
