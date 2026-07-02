from .ride_completion_tracking import ride_completion_summary
from .appointment_transport_tracking import appointment_transport_summary
from .employment_commute_tracking import employment_commute_summary
from .partner_utilization import partner_utilization_summary
from .vehicle_readiness import vehicle_readiness_summary

def mobility_performance_dashboard():
    return {
        "dashboard": "Community Mobility Operations Performance",
        "ride_completion": ride_completion_summary(),
        "appointments": appointment_transport_summary(),
        "employment_commutes": employment_commute_summary(),
        "partner_utilization": partner_utilization_summary(),
        "vehicle_readiness": vehicle_readiness_summary(),
        "status": "operational"
    }

def format_mobility_performance(data):
    rides = data["ride_completion"]
    appts = data["appointments"]
    commutes = data["employment_commutes"]
    vehicles = data["vehicle_readiness"]

    lines = [
        "WATCHMAN COMMUNITY MOBILITY OPERATIONS PERFORMANCE",
        "",
        f"Total Rides: {rides['rides_total']}",
        f"Completed Rides: {rides['completed']}",
        f"Pending Rides: {rides['pending']}",
        f"Missed Rides: {rides['missed']}",
        f"On-Time Rides: {rides['on_time']}",
        "",
        f"Medical Appointments: {appts['medical_appointments']}",
        f"Birmingham Trips: {appts['birmingham_trips']}",
        f"Pending Medical Rides: {appts['pending_medical_rides']}",
        "",
        f"Employment Commutes: {commutes['employment_commutes']}",
        f"Completed Commutes: {commutes['completed_commutes']}",
        f"Missed Commutes: {commutes['missed_commutes']}",
        "",
        f"Active Vehicles: {vehicles['active_vehicles']}",
        f"Vehicles Needed: {vehicles['vehicles_needed']}",
        f"Priority: {vehicles['priority']}",
        "",
        "PARTNER UTILIZATION:"
    ]

    for partner in data["partner_utilization"]:
        lines.append(
            f"- {partner['partner']} | Rides Supported: {partner['rides_supported']} | Best For: {partner['best_for']}"
        )

    return "\n".join(lines)
