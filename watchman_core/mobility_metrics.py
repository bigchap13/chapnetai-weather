from .ride_scheduling import sample_ride_schedule
from .mobility_partners import mobility_partners

def mobility_metrics():
    rides = sample_ride_schedule()
    partners = mobility_partners()

    medical = [r for r in rides if r.get("type") == "Medical"]
    employment = [r for r in rides if r.get("type") == "Employment"]
    missed = [r for r in rides if r.get("status") == "missed"]
    needs_driver = [r for r in rides if r.get("status") == "needs_driver"]
    scheduled = [r for r in rides if r.get("status") == "scheduled"]

    return {
        "rides_total": len(rides),
        "medical_rides": len(medical),
        "employment_rides": len(employment),
        "scheduled_rides": len(scheduled),
        "missed_rides": len(missed),
        "needs_driver": len(needs_driver),
        "mobility_partners": len(partners)
    }
