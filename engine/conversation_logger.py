import json
import os
from datetime import datetime

LOG_FILENAME = "conversation_logs.jsonl"


def _build_log_path(app_dir: str) -> str:
    """
    app_dir pl: 'apps/invoice'
    """
    logs_dir = os.path.join(app_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return os.path.join(logs_dir, LOG_FILENAME)


def log_event(app_dir: str, data: dict):
    """
    app_dir: aktuális app könyvtára (pl. 'apps/invoice')
    data: logolandó tartalom (dict)
    """
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }

    log_path = _build_log_path(app_dir)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
