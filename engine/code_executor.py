#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
# coding: utf-8

# engine/code_executor.py

import pandas as pd
import numpy as np
import sys
import engine.analytics.functions as analytics_functions


def execute_code(code: str, df):
    import matplotlib.pyplot as plt
    import engine.matplotlib_theme as matplotlib_theme

    # 🔑 matplotlib_theme alias – szükséges az AI által generált kódhoz
    sys.modules["matplotlib_theme"] = matplotlib_theme

    exec_env = {
        "__builtins__": __builtins__,
        "df": df,
        "pd": pd,
        "np": np,
        "plt": plt,

        "apply_default_theme": matplotlib_theme.apply_default_theme,
        "format_date_axis": matplotlib_theme.format_date_axis,
        "format_date": matplotlib_theme.format_date,
        "matplotlib_theme": matplotlib_theme,
    }

    # 🔑 analytics/functions.py függvényeinek betöltése
    for name in dir(analytics_functions):
        if name.startswith("_"):
            continue
        obj = getattr(analytics_functions, name)
        if callable(obj):
            exec_env[name] = obj

    # 🔍 Debug / observability: milyen függvényeket lát az AI
    exec_env["_AVAILABLE_FUNCTIONS"] = sorted(
        name for name in exec_env.keys()
        if callable(exec_env[name])
    )


    
    try:
#        exec(code, {}, exec_env)
         exec(code, exec_env)
    except Exception as e:
        raise RuntimeError(f"Hiba a generált kód futtatásakor: {e}")

    if "result" not in exec_env:
        raise ValueError("A kód nem állított be 'result' változót.")

    return exec_env["result"]


# In[ ]:




