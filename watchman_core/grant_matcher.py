from .grant_registry import grant_registry
from .funding_need_mapper import funding_needs

def grant_matches():
    grants = grant_registry()
    needs = funding_needs()

    matches = []

    for need in needs:
        for grant in grants:
            if need["category"] in grant["category"] or grant["category"] in need["category"]:
                matches.append({
                    "need_id": need["need_id"],
                    "need": need["description"],
                    "grant_id": grant["grant_id"],
                    "grant": grant["name"],
                    "priority": need["priority"],
                    "fit": grant["fit"]
                })

    return matches
