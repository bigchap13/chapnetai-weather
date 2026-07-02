def create_sol_id(number, track="Six-Month"):
    return {
        "sol_id": f"SOL-{number:05d}",
        "track": track,
        "status": "active",
        "level": 1
    }
