def transportation_summary(residents):
    total = sum(r.get("transportation_requests", 0) for r in residents)

    return {
        "open_transportation_requests": total,
        "requires_driver_review": total > 0
    }
