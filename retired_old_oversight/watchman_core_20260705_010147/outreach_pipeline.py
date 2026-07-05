PIPELINE = [
    "Identified",
    "Letter Sent",
    "Follow-Up Scheduled",
    "Meeting Scheduled",
    "Donation Offered",
    "Vehicle Received",
    "Partnership Active"
]

def outreach_pipeline_summary():
    return {
        "pipeline_stages": len(PIPELINE),
        "status": "operational"
    }
