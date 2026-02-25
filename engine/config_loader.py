#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""
engine/config_loader.py

Feladat:
- app-specifikus config.yaml beolvasása
- biztonságos fallback-ek
"""

from pathlib import Path
import yaml


def load_config(app_path: str) -> dict:
    """
    Betölti az app config.yaml fájlját.

    Paraméter:
        app_path (str): pl. "apps/insurance_talk"

    Visszatér:
        dict: a config tartalma
    """
    app_dir = Path(app_path).resolve()
    config_file = app_dir / "config.yaml"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Nem található config.yaml itt: {config_file}"
        )

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("A config.yaml nem dictionary formátumú.")

    return config


# In[ ]:




