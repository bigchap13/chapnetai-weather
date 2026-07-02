from .grantfinder_bridge import grantfinder_connection_status
from .grant_matcher import grant_matches

def grantfinder_sync_status():
    return {
        "bridge": grantfinder_connection_status(),
        "matches_ready": len(grant_matches()),
        "sync_status": "ready_for_future_grantfinder_connection"
    }
