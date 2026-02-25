# engine/verbalizer.py

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from openai import OpenAI
import os


VERBALIZER_SYSTEM_PROMPT = """
Te egy adatvizualizációs és riportolási asszisztens vagy.

Feladatod:
Strukturált statisztikai eredményből
rövid, természetes hangvételű, magyar nyelvű választ fogalmazni.

SZABÁLYOK (EZEK KÖTELEZŐEK):
- Ne elemezz és ne következtess.
- Ne adj hozzá új információt.
- Ne magyarázd a módszertant.
- Ne hivatkozz arra, hogy „az adatok szerint”.
- Ne használj felsorolást.
- Ne használj szakzsargont.
- Maximum 1–2 mondat.
- Csak azt írd le, ami a bemenetben szerepel.
"""


def _normalize_result(result: Any) -> Dict:
    """
    Python objektum -> kontrollált, LLM-barát dict.
    """
    # pandas Series
    if isinstance(result, pd.Series):
        return {
            "type": "series",
            "values": result.to_dict(),
            "name": result.name,
        }

    # pandas DataFrame (kicsi)
    if isinstance(result, pd.DataFrame):
        return {
            "type": "dataframe",
            "columns": list(result.columns),
            "rows": result.to_dict(orient="records"),
        }

    # dict
    if isinstance(result, dict):
        return {
            "type": "dict",
            "values": result,
        }

    # lista / tuple
    if isinstance(result, (list, tuple)):
        return {
            "type": "list",
            "values": list(result),
        }

    # fallback – ezt ritkán kéne elérni
    return {
        "type": "scalar",
        "value": str(result),
    }


def verbalize_result(
    *,
    question: str,
    result: Any,
    model: str = "gpt-4.1",
    temperature: float = 0.2,
) -> str:
    """
    Strukturált eredmény -> szép magyar nyelvű válasz.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    payload = _normalize_result(result)

    messages = [
        {
            "role": "system",
            "content": VERBALIZER_SYSTEM_PROMPT.strip(),
        },
        {
            "role": "user",
            "content": f"""
Kérdés:
{question}

Eredmény (strukturált):
{payload}
""".strip(),
        },
    ]

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )

    return resp.choices[0].message.content.strip()
