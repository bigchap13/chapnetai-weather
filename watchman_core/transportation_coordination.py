def transportation_assessment(resident):
    return {
        "sol_id": resident.get("sol_id"),
        "has_vehicle": resident.get("has_vehicle", False),
        "needs_transportation": not resident.get("has_vehicle", False),
        "status": "assessment_complete"
    }

def transportation_plan(resident):
    assessment = transportation_assessment(resident)

    if not assessment["needs_transportation"]:
        return {
            "sol_id": resident.get("sol_id"),
            "plan": "Personal Vehicle",
            "status": "ready"
        }

    return {
        "sol_id": resident.get("sol_id"),
        "plan": "Transportation Assistance Required",
        "status": "action_needed"
    }
