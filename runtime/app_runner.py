# runtime/app_runner.py

import streamlit as st
from engine.config_loader import load_config
from engine.data_loader import load_data
from engine.prompt_engine import build_prompt
from runtime.ui import render_app_ui


def run_app(app_path: str):
    # app_path: pl. "apps/market_research"
    cfg = load_config(app_path)
    df = load_data(app_path, cfg["data"])
    prompt = build_prompt(app_path)

    # UI (univerzális)
    render_app_ui(cfg, df, prompt, app_path)
