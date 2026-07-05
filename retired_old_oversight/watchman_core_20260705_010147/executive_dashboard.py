from watchman.ai_oversight import ai_oversight_snapshot
from watchman.jj_integration import sample_residents, jj_summary
from watchman.jj_transportation import transportation_summary
from watchman.smart_home_engine import smart_home_status
from watchman.telegram_engine import telegram_status

def executive_dashboard():
    residents = sample_residents()

    return {
        "system_status": "GREEN",
        "ai_oversight": ai_oversight_snapshot(),
        "resident_summary": jj_summary(residents),
        "transportation": transportation_summary(residents),
        "smart_home": smart_home_status(),
        "telegram": telegram_status()
    }
