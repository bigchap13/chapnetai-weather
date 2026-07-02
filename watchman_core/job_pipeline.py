PIPELINE_STAGES = [
    "Interested",
    "Applied",
    "Interview Scheduled",
    "Interview Completed",
    "Offer Received",
    "Hired",
    "Retained 30 Days"
]

def create_pipeline_item(sol_id, job_id, stage="Interested"):
    return {
        "sol_id": sol_id,
        "job_id": job_id,
        "stage": stage
    }

def sample_pipeline():
    return [
        create_pipeline_item("SOL-00001", "JOB-001", "Applied"),
        create_pipeline_item("SOL-00002", "JOB-002", "Interview Scheduled")
    ]
