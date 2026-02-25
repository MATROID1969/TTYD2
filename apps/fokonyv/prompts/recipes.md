# Főkönyv – Recepteknél használt minták

=== RECEPTEK (példák) ===

1. Kérdés: Készíts egy táblázatot, ami havi szintű árbevételek alapján rendezi sorba hónapokat.
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# Másolat az adatokból
df_tmp = df.copy()

# Hónap kanonikus sorrend (magyar)
HONAP_SORREND = [
    "Január", "Február", "Március", "Április",
    "Május", "Június", "Július", "Augusztus",
    "Szeptember", "Október", "November", "December"
]

# Érték biztos numerikussá alakítása (robosztus)
df_tmp["Érték"] = pd.to_numeric(df_tmp["Érték"], errors="coerce")

# Bevétel flag: Főkönyviszám első számjegye == 9
df_tmp["Főkönyviszám"] = df_tmp["Főkönyviszám"].astype(str)
df_tmp["_is_bevetel"] = df_tmp["Főkönyviszám"].str.strip().str[0].eq("9")

# Csak árbevétel (META alapértelmezés) + csak bevétel jelleg (9-es számlaosztály)
df_rev = df_tmp[
    (df_tmp["Főkönyv3"] == "Belföldi értékesítés nettó árbevétele") &
    (df_tmp["_is_bevetel"]) &
    (df_tmp["Hónap"].notna()) &
    (df_tmp["Érték"].notna())
].copy()

# Havi árbevétel összegzés (előjel korrekció: bevételnél mínusz → szorozzuk -1-el)
monthly_rev = (
    df_rev
    .groupby("Hónap", as_index=False)["Érték"]
    .sum()
    .rename(columns={"Érték": "Árbevétel"})
)

monthly_rev["Árbevétel"] = monthly_rev["Árbevétel"] * (-1)

# Hónap rendezéséhez kategória
monthly_rev["Hónap"] = pd.Categorical(
    monthly_rev["Hónap"],
    categories=HONAP_SORREND,
    ordered=True
)

# Rangsorolás árbevétel alapján (csökkenő)
monthly_rev = monthly_rev.sort_values("Árbevétel", ascending=False).reset_index(drop=True)

# Eredmény
result = monthly_rev[["Hónap", "Árbevétel"]]

```

2. Kérdés: Állítsd sorba havi szinten a munkabér költséget
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# Másolat az adatokból
df_tmp = df.copy()

# Hónap kanonikus sorrend (magyar)
HONAP_SORREND = [
    "Január", "Február", "Március", "Április",
    "Május", "Június", "Július", "Augusztus",
    "Szeptember", "Október", "November", "December"
]

# Érték biztos numerikussá alakítása (robosztus)
df_tmp["Érték"] = pd.to_numeric(df_tmp["Érték"], errors="coerce")

# Főkönyviszám tisztítás: csak számjegyek (biztos első számjegy vizsgálathoz)
df_tmp["Főkönyviszám"] = (
    df_tmp["Főkönyviszám"]
    .astype(str)
    .str.extract(r"(\d+)", expand=False)
)

# Költség/ráfordítás jelleg: NEM 9-es számlaosztály
df_tmp["_is_koltseg_vagy_raforditas"] = df_tmp["Főkönyviszám"].str[0].ne("9")

# Munkabér költség: a META szerinti konkrét tételnév
df_wage = df_tmp[
    (df_tmp["Főkönyvi_tétel"] == "Bérköltség") &
    (df_tmp["_is_koltseg_vagy_raforditas"]) &
    (df_tmp["Hónap"].notna()) &
    (df_tmp["Érték"].notna())
].copy()

# Havi munkabér költség összegzés (költségnél az Érték eleve pozitív)
monthly_wage = (
    df_wage
    .groupby("Hónap", as_index=False)["Érték"]
    .sum()
    .rename(columns={"Érték": "Munkabér_költség"})
)

# Hónap rendezéséhez kategória (stabil megjelenítéshez)
monthly_wage["Hónap"] = pd.Categorical(
    monthly_wage["Hónap"],
    categories=HONAP_SORREND,
    ordered=True
)

# Rangsorolás havi munkabér költség alapján (csökkenő)
monthly_wage = (
    monthly_wage
    .sort_values("Munkabér_költség", ascending=False)
    .reset_index(drop=True)
)

# Kimenet
result = monthly_wage[["Hónap", "Munkabér_költség"]]

```

3. Kérdés: Nézzük meg az árbevétel / munkabér ktg arányát
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np

# Másolat az adatokból
df_tmp = df.copy()

# Érték biztos numerikussá alakítása
df_tmp["Érték"] = pd.to_numeric(df_tmp["Érték"], errors="coerce")

# Főkönyviszám tisztítása: csak számjegyek
df_tmp["Főkönyviszám"] = (
    df_tmp["Főkönyviszám"]
    .astype(str)
    .str.extract(r"(\d+)", expand=False)
)

# Bevétel sorok: 9-es számlaosztály
df_tmp["_is_bevetel"] = df_tmp["Főkönyviszám"].str[0].eq("9")

# Teljes időszaki bevétel (minden 9-es tétel) - előjel korrekció (-1)
total_bevetel = (
    df_tmp[
        df_tmp["_is_bevetel"] &
        df_tmp["Érték"].notna()
    ]["Érték"]
    .sum()
) * (-1)

# Teljes időszaki munkabér költség (META szerinti tétel)
total_munkaber = (
    df_tmp[
        (df_tmp["Főkönyvi_tétel"] == "Bérköltség") &
        df_tmp["Érték"].notna()
    ]["Érték"]
    .sum()
)

# Hányados: munkabér / bevétel (bevétel a nevezőben)
if (pd.isna(total_bevetel)) or (float(total_bevetel) == 0.0):
    result = np.nan
else:
    result = float(total_munkaber) / float(total_bevetel)

```


4. Kérdés: Rajzolj egy oszlop diagramot, ami havi szinten mutatja az "Anyagjellegû ráfordítások" összegét! 
```python

import warnings; warnings.filterwarnings("ignore")
from matplotlib_theme import apply_default_theme
apply_default_theme()

import matplotlib.pyplot as plt
import pandas as pd

# Másolat az adatokból
df_tmp = df.copy()

# Hónap kanonikus sorrend (magyar)
HONAP_SORREND = [
    "Január", "Február", "Március", "Április",
    "Május", "Június", "Július", "Augusztus",
    "Szeptember", "Október", "November", "December"
]

# Érték biztos numerikussá alakítása
df_tmp["Érték"] = pd.to_numeric(df_tmp["Érték"], errors="coerce")

# Csak anyagjellegű ráfordítások
df_mat = df_tmp[
    (df_tmp["Főkönyv3"] == "Anyagjellegû ráfordítások") &
    (df_tmp["Hónap"].notna()) &
    (df_tmp["Érték"].notna())
].copy()

# Havi összegzés
monthly_mat = (
    df_mat
    .groupby("Hónap", as_index=False)["Érték"]
    .sum()
)

# Hónap rendezése
monthly_mat["Hónap"] = pd.Categorical(
    monthly_mat["Hónap"],
    categories=HONAP_SORREND,
    ordered=True
)

monthly_mat = monthly_mat.sort_values("Hónap")

# Oszlopdiagram
fig, ax = plt.subplots(figsize=(8,3))

ax.bar(
    monthly_mat["Hónap"].astype(str),
    monthly_mat["Érték"]
)

ax.set_title("Anyagjellegű ráfordítások – havi bontásban")
ax.set_xlabel("Hónap")
ax.set_ylabel("Összeg (Ft)")

result = fig

```


5. Kérdés: Melyik hónapban volt a legkisebb az "Anyagköltség"? 
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# Másolat az adatokból
df_tmp = df.copy()

# Érték biztos numerikussá alakítása
df_tmp["Érték"] = pd.to_numeric(df_tmp["Érték"], errors="coerce")

# Csak anyagköltség sorok
df_mat = df_tmp[
    (df_tmp["Főkönyv3"] == "Anyagköltség") &
    (df_tmp["Hónap"].notna()) &
    (df_tmp["Érték"].notna())
].copy()

# Havi anyagköltség összegzés
monthly_mat = (
    df_mat
    .groupby("Hónap", as_index=False)["Érték"]
    .sum()
    .rename(columns={"Érték": "Anyagköltség"})
)

# Legkisebb értékű hónap
if len(monthly_mat) == 0:
    result = None
else:
    idx = monthly_mat["Anyagköltség"].idxmin()
    row = monthly_mat.loc[idx]

    result = {
        "Honap": str(row["Hónap"]),
        "Anyagkoltseg": float(row["Anyagköltség"])
    }


```
