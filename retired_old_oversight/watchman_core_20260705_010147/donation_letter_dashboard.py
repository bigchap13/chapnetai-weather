from .donation_letter_registry import sample_donation_letter_records
from .vehicle_donation_letter import generate_vehicle_donation_letter

def donation_letter_dashboard():
    records = sample_donation_letter_records()

    return {
        "dashboard": "Vehicle Donation Letter Generator",
        "letters": records,
        "letters_ready": len([r for r in records if r["status"] == "draft_ready"]),
        "sample_letter": generate_vehicle_donation_letter("Jasper Area Dealership", "Community Partner"),
        "status": "operational"
    }

def format_donation_letter_dashboard(data):
    lines = [
        "WATCHMAN VEHICLE DONATION LETTER GENERATOR",
        "",
        f"Letters Ready: {data['letters_ready']}",
        "",
        "TARGETS:"
    ]

    for record in data["letters"]:
        lines.append(
            f"- {record['target']} | Need: {record['vehicle_need']} | Status: {record['status']}"
        )

    lines.append("")
    lines.append("SAMPLE LETTER:")
    lines.append(data["sample_letter"])

    return "\n".join(lines)
