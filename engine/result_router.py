#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# engine/result_router.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import matplotlib.figure as mpl_fig

try:
    import matplotlib.axes as mpl_axes
except Exception:
    mpl_axes = None

try:
    import pandas as pd
except Exception:
    pd = None



@dataclass
class RoutedResult:
    kind: str  # "figure" | "table" | "data"
    figure: Optional[mpl_fig.Figure] = None
    data: Any = None


def route_result(obj: Any) -> RoutedResult:
    # 1) Figure
    if isinstance(obj, mpl_fig.Figure):
        return RoutedResult(kind="figure", figure=obj)

    # 2) Axes -> Figure
    if mpl_axes is not None and isinstance(obj, mpl_axes.Axes):
        return RoutedResult(kind="figure", figure=obj.figure)

    # 3) Pandas DataFrame -> table
    if pd is not None and isinstance(obj, pd.DataFrame):
        return RoutedResult(kind="table", data=obj)

    # 4) Everything else -> data
    return RoutedResult(kind="data", data=obj)

