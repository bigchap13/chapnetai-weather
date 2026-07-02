def wellness_status(resident):
    status = resident.get("wellness", "stable")

    if status == "urgent":
        return {"level": "red", "message": "Immediate staff follow-up required."}

    if status in ["struggling", "needs_support"]:
        return {"level": "yellow", "message": "Support follow-up recommended."}

    return {"level": "green", "message": "Resident appears stable."}
