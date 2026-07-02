from .vehicle_donation_outreach import dealership_outreach_targets
from .vehicle_donation_pipeline import sample_vehicle_donation_pipeline
from .fleet_readiness import fleet_readiness_status

def fleet_dashboard():
    targets = dealership_outreach_targets()
    pipeline = sample_vehicle_donation_pipeline()
    readiness = fleet_readiness_status()

    return {
        "dashboard": "Vehicle Donation & Fleet Readiness",
        "dealership_targets": len(targets),
        "donation_pipeline_items": len(pipeline),
        "fleet_readiness": readiness,
        "targets": targets,
        "pipeline": pipeline,
        "status": "operational"
    }

def format_fleet_dashboard(data):
    readiness = data["fleet_readiness"]

    lines = [
        "WATCHMAN VEHICLE DONATION & FLEET READINESS",
        "",
        f"Dealership Targets: {data['dealership_targets']}",
        f"Donation Pipeline Items: {data['donation_pipeline_items']}",
        f"Active Vehicles: {readiness['active_vehicles']}",
        f"Planned Vehicles: {readiness['planned_vehicles']}",
        f"Vehicles Needed: {readiness['vehicles_needed']}",
        f"Priority Vehicle: {readiness['priority_vehicle']}",
        f"Readiness Status: {readiness['readiness_status']}",
        "",
        "OUTREACH TARGETS:"
    ]

    for target in data["targets"]:
        lines.append(
            f"- {target['name']} | {target['location']} | Need: {target['vehicle_need']} | Status: {target['status']}"
        )

    return "\n".join(lines)
