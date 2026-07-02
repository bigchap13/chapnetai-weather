def sample_ride_completion_records():
    return [
        {
            "ride_id": "RIDE-001",
            "type": "Employment",
            "status": "completed",
            "on_time": True
        },
        {
            "ride_id": "RIDE-002",
            "type": "Medical",
            "status": "pending",
            "on_time": None
        }
    ]

def ride_completion_summary():
    records = sample_ride_completion_records()

    completed = [r for r in records if r["status"] == "completed"]
    pending = [r for r in records if r["status"] == "pending"]
    missed = [r for r in records if r["status"] == "missed"]
    on_time = [r for r in completed if r["on_time"] is True]

    return {
        "rides_total": len(records),
        "completed": len(completed),
        "pending": len(pending),
        "missed": len(missed),
        "on_time": len(on_time)
    }
