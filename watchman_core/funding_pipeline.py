PIPELINE = [
    "Identified",
    "Research Needed",
    "Eligible",
    "Drafting",
    "Submitted",
    "Awarded",
    "Declined"
]

def funding_pipeline_records():
    return [
        {
            "grant_id": "GRANT-001",
            "stage": "Identified",
            "next_action": "Review transportation eligibility"
        },
        {
            "grant_id": "GRANT-002",
            "stage": "Identified",
            "next_action": "Review workforce eligibility"
        }
    ]
