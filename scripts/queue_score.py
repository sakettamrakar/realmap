import argparse

def main():
    parser = argparse.ArgumentParser(description="Queue project scoring jobs.")
    parser.add_argument("--project_id", type=str, required=True, help="Project ID or 'all'")
    parser.add_argument("--batch_size", type=int, default=10, help="Batch size for processing")
    
    args = parser.parse_args()
    
    print(f"Queuing scoring job for Project: {args.project_id} with Batch Size: {args.batch_size}")
    
    import requests
    
    api_url = "http://localhost:8001/api/v1/score/project"
    
    if args.project_id.lower() == "all":
        print("Batch processing 'all' not yet implemented in API. Skipping.")
        return

    try:
        response = requests.post(api_url, json={"project_id": args.project_id})
        response.raise_for_status()
        data = response.json()
        print(f"Job successfully queued. Task ID: {data.get('task_id')}")
    except Exception as e:
        print(f"Error queuing job: {e}")

if __name__ == "__main__":
    main()
