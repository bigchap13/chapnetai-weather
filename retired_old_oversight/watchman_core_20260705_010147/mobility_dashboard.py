from .mobility_partners import mobility_partners
from .vehicle_donations import vehicle_donation_registry
from .ride_requests import sample_ride_requests
from .medical_transport import medical_transport_summary
from .employment_transport import employment_transport_summary

def mobility_dashboard():
    partners = mobility_partners()
    donations = vehicle_donation_registry()
    rides = sample_ride_requests()

    return {
        "partners": len(partners),
        "vehicle_donations": len(donations),
        "ride_requests": len(rides),
        "medical": medical_transport_summary(),
        "employment": employment_transport_summary(),
        "status": "operational"
    }

def format_mobility_dashboard(data):
    return f"""
WATCHMAN COMMUNITY MOBILITY NETWORK

Partners: {data['partners']}
Vehicle Donation Prospects: {data['vehicle_donations']}
Ride Requests: {data['ride_requests']}

Medical Requests: {data['medical']['medical_requests']}
Employment Requests: {data['employment']['employment_requests']}

Status: {data['status']}
""".strip()
