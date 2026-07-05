PIPELINE_STAGES = [
    "Identified",
    "Letter Prepared",
    "Contacted",
    "Follow-Up Needed",
    "Donation Offered",
    "Inspection Needed",
    "Accepted",
    "Declined"
]

def sample_vehicle_donation_pipeline():
    return [
        {
            "target_id": "DLR-001",
            "stage": "Identified",
            "vehicle_type": "Passenger Van",
            "status": "open"
        }
    ]
