#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# engine/ai_engine.py

import os
import re
from openai import OpenAI


def generate_code(
    user_question: str,
    system_prompt: str,
    model: str = "gpt-4.1",
    temperature: float = 0.0,
) -> str:
    """
    LLM hívás → Python kód generálása
    """

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ],
        temperature=temperature,
    )

    msg = response.choices[0].message.content.strip()

    # ```python ... ``` blokk kivágása
    matches = re.findall(r"```python(.*?)```", msg, flags=re.S)
    code = matches[-1].strip() if matches else msg

    # Magyarázó sorok kiszűrése
    clean_lines = []
    for line in code.splitlines():
        if not re.match(r"^\s*(Íme|A következő|Megoldás|#\!)", line, re.I):
            clean_lines.append(line)

    return "\n".join(clean_lines).strip()

