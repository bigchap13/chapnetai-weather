def maintenance_readiness_check(vehicle):
    return {
        "vehicle_id": vehicle.get("vehicle_id", "UNKNOWN"),
        "insurance_needed": True,
        "inspection_needed": True,
        "registration_needed": True,
        "maintenance_status": "pending"
    }
