# engine/question_rewriter.py

import os
from openai import OpenAI

REWRITE_SYSTEM_PROMPT = """
Te egy senior magyar adatelemző asszisztens vagy.

Feladat:
Két felhasználói kérdésből készíts egyetlen, teljes, egyértelmű elemző kérdést.

Bemenet:
- BASE: az eredeti (teljes) kérdés
- FOLLOWUP: a ráépülő, rövidítő / szűkítő kérdés

Kimenet:
- csak és kizárólag egy darab, magyar mondat/kérdés (nincs magyarázat, nincs lista)
- legyen teljesen önállóan értelmezhető
- tartalmazza a szűkítést (pl. „nők körében”, „budapestiek között”, stb.)
- NE kérj vissza, NE tegyél fel kérdést, csak fogalmazz át

Fontos:
Ha a FOLLOWUP valójában új elemzés (pl. diagram, összehasonlítás, trend), akkor is fogalmazz egyetlen kérdést, ami tükrözi ezt.
"""

def rewrite_question(base_question: str, followup_question: str, model: str = "gpt-4.1") -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    user_msg = f"""BASE:
{base_question}

FOLLOWUP:
{followup_question}

Írd meg az összevont, végleges kérdést:"""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,
    )

    merged = resp.choices[0].message.content.strip()
    # kis tisztítás
    merged = merged.replace("„", '"').replace("”", '"')
    return merged
