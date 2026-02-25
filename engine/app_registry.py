from pathlib import Path
import yaml


def list_apps(apps_dir="apps"):
    """
    Visszaadja az összes elérhető appot az apps/ mappából.
    Egy app = könyvtár, amiben van config.yaml
    """
    apps = []

    base = Path(apps_dir)
    if not base.exists():
        return apps

    for app_dir in base.iterdir():
        if not app_dir.is_dir():
            continue

        cfg_path = app_dir / "config.yaml"
        if not cfg_path.exists():
            continue

        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        app_info = {
            "id": cfg["app"]["id"],
            "name": cfg["app"]["name"],
            "description": cfg["app"].get("description", ""),
            "path": str(app_dir),
        }

        apps.append(app_info)

    return apps
