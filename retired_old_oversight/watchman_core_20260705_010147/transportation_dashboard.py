from .transportation_registry import available_transport_resources

def transportation_dashboard():
    return {
        "resources": available_transport_resources(),
        "resource_count": len(available_transport_resources()),
        "status": "operational"
    }
