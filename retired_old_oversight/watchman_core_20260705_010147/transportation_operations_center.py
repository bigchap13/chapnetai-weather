from .ride_scheduling import sample_ride_schedule
from .driver_assignments import sample_driver_assignments
from .vehicle_assignments import sample_vehicle_assignments
from .partner_dispatch import partner_dispatch_options

def transportation_operations_center():
    rides = sample_ride_schedule()
    drivers = sample_driver_assignments()
    vehicles = sample_vehicle_assignments()
    partners = partner_dispatch_options()

    open_rides = [r for r in rides if r["status"] in ["open", "needs_driver"]]
    scheduled_rides = [r for r in rides if r["status"] == "scheduled"]
    available_drivers = [d for d in drivers if d["status"] == "available"]

    return {
        "center": "Transportation Operations Center",
        "rides_total": len(rides),
        "open_rides": len(open_rides),
        "scheduled_rides": len(scheduled_rides),
        "available_drivers": len(available_drivers),
        "vehicles": len(vehicles),
        "partners": len(partners),
        "rides": rides,
        "drivers": drivers,
        "vehicles_list": vehicles,
        "partners_list": partners,
        "status": "operational"
    }

def format_transportation_center(data):
    lines = [
        "WATCHMAN TRANSPORTATION OPERATIONS CENTER",
        "",
        f"Total Rides: {data['rides_total']}",
        f"Open / Needs Driver: {data['open_rides']}",
        f"Scheduled Rides: {data['scheduled_rides']}",
        f"Available Drivers: {data['available_drivers']}",
        f"Vehicles: {data['vehicles']}",
        f"Partners: {data['partners']}",
        "",
        "RIDES:"
    ]

    for ride in data["rides"]:
        lines.append(
            f"- {ride['ride_id']} | {ride['type']} | {ride['destination']} | {ride['time']} | {ride['status']}"
        )

    return "\n".join(lines)
