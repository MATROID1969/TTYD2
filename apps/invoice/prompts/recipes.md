# Invoice – Recepteknél használt minták

=== RECEPTEK (példák) ===

1. Kérdés: 2023-ban hány számla lett kiállítva?
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# Paraméter
YEAR = 2023

# Másolat az adatokból
df_tmp = df.copy()

# Kiállítás dátumának biztos kezelése
df_tmp["posting_date"] = pd.to_datetime(
    df_tmp["posting_date"], errors="coerce"
)

# Szűrés: 2023-ban kiállított számlák
df_filtered = df_tmp[
    df_tmp["posting_date"].dt.year == YEAR
]

# Eredmény
result = int(len(df_filtered))

```

2. Kérdés: Melyik ügyfélnek lett kiállítva legtöbb számla? 
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# Másolat az adatokból
df_tmp = df.copy()

# Csak értelmezhető ügyfélnevek
df_tmp = df_tmp[
    df_tmp["customer_name"].notna()
].copy()

# Számlák darabszáma ügyfelenként
counts = (
    df_tmp
    .groupby("customer_name")
    .size()
    .sort_values(ascending=False)
)

# Legtöbb számlával rendelkező ügyfél
top_customer = str(counts.index[0]) if len(counts) > 0 else None
top_count = int(counts.iloc[0]) if len(counts) > 0 else 0

# Eredmény
result = {
    "ugyfel": top_customer,
    "szamlak_szama": top_count
}

```


3. Kérdés: Rajzolj egy sávdiagramot, ami az 5 legnagyobb vevőt mutatja számlaszám alapján! 
```python

import warnings; warnings.filterwarnings("ignore")
from matplotlib_theme import apply_default_theme
apply_default_theme()
import matplotlib.pyplot as plt
import pandas as pd

TOP_N = 5

# Másolat az adatokból
df_tmp = df.copy()

# Csak értelmezhető ügyfélnevek
df_tmp = df_tmp[
    df_tmp["customer_name"].notna()
].copy()

# Számlák darabszáma ügyfelenként
counts = (
    df_tmp
    .groupby("customer_name")
    .size()
    .sort_values(ascending=False)
    .head(TOP_N)
)

# Ábrázoláshoz (fordított sorrend a jobb olvashatóságért)
counts = counts.sort_values(ascending=True)

customers = counts.index.astype(str)
values = counts.values.astype(int)

# SÁVDIAGRAM (HORIZONTÁLIS)
fig, ax = plt.subplots(figsize=(8,3))
ax.barh(customers, values)

ax.set_title("Top 5 vevő számlaszám alapján")
ax.set_xlabel("Számlák száma")
ax.set_ylabel("Ügyfél")

result = fig

```

4. Kérdés: A 2024-es számlák hány százalék lett fizetési határidőn túl legalább 3 nappal kifizetve? 
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# Paraméterek
YEAR = 2024
MIN_DELAY_DAYS = 3

# Másolat az adatokból
df_tmp = df.copy()

# Dátummezők biztos kezelése
df_tmp["posting_date"] = pd.to_datetime(
    df_tmp["posting_date"], errors="coerce"
)
df_tmp["due_in_date"] = pd.to_datetime(
    df_tmp["due_in_date"], errors="coerce"
)
df_tmp["clear_date"] = pd.to_datetime(
    df_tmp["clear_date"], errors="coerce"
)

# Csak 2024-ben kiállított számlák
df_2024 = df_tmp[
    df_tmp["posting_date"].dt.year == YEAR
].copy()

total_n = len(df_2024)

if total_n == 0:
    result = 0.0
else:
    # Csak ténylegesen kifizetett számlák
    df_paid = df_2024[
        df_2024["clear_date"].notna() &
        df_2024["due_in_date"].notna()
    ].copy()

    # Fizetési késés napokban
    df_paid["delay_days"] = kesedelmes_napok(
        df_paid["due_in_date"],
        df_paid["clear_date"])


    # Legalább 3 napos késéssel fizetettek
    delayed = df_paid[
        df_paid["delay_days"] >= MIN_DELAY_DAYS
    ]

    pct = len(delayed) / total_n * 100
    result = round(float(pct), 2)

```


5. Kérdés: Rajzolj egy vonal diagramot, ami havi bontásban mutatja, hogy az adott hónapban kiállított számlák hány százaléka volt késedelmes kifizetésű? 
```python
import warnings; warnings.filterwarnings("ignore")
from matplotlib_theme import apply_default_theme
apply_default_theme()
import matplotlib.pyplot as plt
import pandas as pd

# Paraméter
MIN_DELAY_DAYS = 1  # késedelmes = legalább 1 nap csúszás

# Másolat az adatokból
df_tmp = df.copy()

# Dátummezők biztos kezelése
df_tmp["posting_date"] = pd.to_datetime(
    df_tmp["posting_date"], errors="coerce"
)
df_tmp["due_in_date"] = pd.to_datetime(
    df_tmp["due_in_date"], errors="coerce"
)
df_tmp["clear_date"] = pd.to_datetime(
    df_tmp["clear_date"], errors="coerce"
)

# Csak értelmezhető kiállítási dátum
df_tmp = df_tmp[
    df_tmp["posting_date"].notna()
].copy()

# Hónap képzése
df_tmp["Honap"] = df_tmp["posting_date"].dt.to_period("M")

records = []

for honap, sub in df_tmp.groupby("Honap"):
    total = len(sub)

    if total == 0:
        continue

    # Csak ténylegesen kifizetett számlák, ahol van határidő
    paid = sub[
        sub["clear_date"].notna() &
        sub["due_in_date"].notna()
    ].copy()

    if len(paid) == 0:
        pct_delayed = 0.0
    else:
        # Késés napokban
        paid["delay_days"] = kesedelmes_napok(
            paid["due_in_date"],
            paid["clear_date"])


        delayed = paid[
            paid["delay_days"] >= MIN_DELAY_DAYS
        ]

        pct_delayed = len(delayed) / total * 100

    records.append({
        "Honap": honap.to_timestamp(how="start"),
        "Keses_pct": float(pct_delayed)
    })

df_plot = pd.DataFrame(records)

# Idősoros vonaldiagram
fig, ax = plt.subplots(figsize=(8,3))
ax.plot(
    df_plot["Honap"],
    df_plot["Keses_pct"],
    marker="o"
)

ax.set_title("Késedelmesen kifizetett számlák aránya – havi bontásban")
ax.set_ylabel("%")
ax.set_xlabel("Hónap")

result = fig

```

6. Kérdés: Mutasd meg azt az 5 Vevőt, amelyeknek körében a 2025-ös számlák legnagyobb arányban kerültek késedelmes kifizetésbe!  
```python

import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# Paraméterek
YEAR = 2025
MIN_DELAY_DAYS = 1   # késedelmes = legalább 1 nap csúszás
TOP_N = 5

# Másolat az adatokból
df_tmp = df.copy()

# Dátummezők biztos kezelése
df_tmp["posting_date"] = pd.to_datetime(
    df_tmp["posting_date"], errors="coerce"
)
df_tmp["due_in_date"] = pd.to_datetime(
    df_tmp["due_in_date"], errors="coerce"
)
df_tmp["clear_date"] = pd.to_datetime(
    df_tmp["clear_date"], errors="coerce"
)

# Csak 2025-ben kiállított számlák + értelmezhető vevő
df_2025 = df_tmp[
    (df_tmp["posting_date"].dt.year == YEAR) &
    (df_tmp["customer_name"].notna())
].copy()

# Csak olyan számlák, ahol van határidő
df_2025 = df_2025[
    df_2025["due_in_date"].notna()
].copy()

# Késés napokban (csak ahol kifizették)
df_2025["delay_days"] = kesedelmes_napok(
    df_2025["due_in_date"],
    df_2025["clear_date"])


# Késedelmes fizetés flag
df_2025["kesedelmes"] = (
    df_2025["delay_days"] >= MIN_DELAY_DAYS
)

# Ügyfelenkénti arány számítása
stats = (
    df_2025
    .groupby("customer_name")["kesedelmes"]
    .agg(
        osszes_szamla="count",
        kesedelmes_szamla="sum"
    )
)

# Arány (%)
stats["kesedelmes_arany_pct"] = (
    stats["kesedelmes_szamla"] / stats["osszes_szamla"] * 100
)

# Csak ahol van legalább 1 számla
stats = stats[
    stats["osszes_szamla"] > 0
]

# TOP 5 legrosszabb arány szerint
top5 = (
    stats
    .sort_values("kesedelmes_arany_pct", ascending=False)
    .head(TOP_N)
)

# Eredmény strukturált formában
result = {
    str(idx): round(float(row["kesedelmes_arany_pct"]), 2)
    for idx, row in top5.iterrows()
}

```

7. Kérdés: Ha egy cégnek az előző számlája késve lett kifizetve, akkor mekkora a valószínűsége, hogy az aktuális számla késve lesz kifizetve?   
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# Paraméter: késedelmes = legalább 1 nap csúszás
MIN_DELAY_DAYS = 1

df_tmp = df.copy()

# Dátummezők biztos kezelése
df_tmp["posting_date"] = pd.to_datetime(df_tmp["posting_date"], errors="coerce")
df_tmp["due_in_date"] = pd.to_datetime(df_tmp["due_in_date"], errors="coerce")
df_tmp["clear_date"] = pd.to_datetime(df_tmp["clear_date"], errors="coerce")

# Csak ahol tudjuk értelmezni a sorrendet és a késést
# (csak ténylegesen kifizetett számlákon értelmezhető a késés)
df_tmp = df_tmp[
    df_tmp["customer_name"].notna() &
    df_tmp["posting_date"].notna() &
    df_tmp["due_in_date"].notna() &
    df_tmp["clear_date"].notna()
].copy()

# Késés napokban és késedelmes flag
df_tmp["delay_days"] = kesedelmes_napok(
    df_tmp["due_in_date"],
    df_tmp["clear_date"])

df_tmp["delayed"] = df_tmp["delay_days"] >= MIN_DELAY_DAYS


# Rendezés: "előző számla" = ugyanazon vevő előző kiállított számlája
df_tmp = df_tmp.sort_values(
    ["customer_name", "posting_date", "invoice_nr"]
)

# Előző számla késedelmes flag vevőnként
df_tmp["prev_delayed"] = (
    df_tmp
    .groupby("customer_name")["delayed"]
    .shift(1)
)

# Csak azok a sorok, ahol van előző számla is
df_pairs = df_tmp[
    df_tmp["prev_delayed"].notna()
].copy()

# Feltételes bázis: előző számla késedelmes volt
cond_base = df_pairs[
    df_pairs["prev_delayed"] == True
]

base_n = int(len(cond_base))
delayed_now_n = int(cond_base["delayed"].sum())

if base_n == 0:
    prob_pct = 0.0
else:
    prob_pct = delayed_now_n / base_n * 100

# Egységes, tanítható eredményformátum
result = {
    "valoszinuseg_pct": round(float(prob_pct), 2),
    "bazis_db": base_n,
    "kesedelmes_aktualis_db": delayed_now_n
}
    
```

8. Kérdés: Rajzolj egy vonaldiagramot, ami a számla bruttó összege fügvényében mutatja a késve fizetés valószínűségét!   
```python
import warnings; warnings.filterwarnings("ignore")
from matplotlib_theme import apply_default_theme
apply_default_theme()

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import numpy as np

# --------------------
# Paraméterek
# --------------------
BIN_SIZE = 100_000          # 100 ezer Ft-os bin-ek
MAX_AMOUNT = 10_000_000     # 10 M Ft felett összevonjuk
MIN_DELAY_DAYS = 1          # késedelmes = legalább 1 nap

# --------------------
# Adatelőkészítés
# --------------------
df_tmp = df.copy()

# Dátummezők biztos kezelése
df_tmp["due_in_date"] = pd.to_datetime(
    df_tmp["due_in_date"], errors="coerce"
)
df_tmp["clear_date"] = pd.to_datetime(
    df_tmp["clear_date"], errors="coerce"
)

# Csak értelmezhető számlák:
# - van bruttó összeg
# - van határidő
# - van kifizetési dátum
df_tmp = df_tmp[
    df_tmp["Brutto"].notna() &
    df_tmp["due_in_date"].notna() &
    df_tmp["clear_date"].notna()
].copy()

# --------------------
# Késés számítása
# --------------------
df_tmp["delay_days"] = kesedelmes_napok(
    df_tmp["due_in_date"],
    df_tmp["clear_date"])


df_tmp["delayed"] = df_tmp["delay_days"] >= MIN_DELAY_DAYS

# --------------------
# Bruttó összeg kezelése
# --------------------
# Visszajáróknál lehet negatív → abs
df_tmp["brutto_abs"] = df_tmp["Brutto"].abs()

# 0 értékek kizárása
df_tmp = df_tmp[df_tmp["brutto_abs"] > 0].copy()

# Felső cap (10M+ egy binbe)
df_tmp["brutto_capped"] = df_tmp["brutto_abs"].clip(upper=MAX_AMOUNT)

# --------------------
# Bin-elés
# --------------------
bins = np.arange(0, MAX_AMOUNT + BIN_SIZE, BIN_SIZE)
labels = bins[:-1]

df_tmp["amount_bin"] = pd.cut(
    df_tmp["brutto_capped"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

# --------------------
# Bin-enkénti statisztika
# --------------------
stats = (
    df_tmp
    .groupby("amount_bin")["delayed"]
    .agg(
        osszes="count",
        kesedelmes="sum"
    )
    .reset_index()
)

# Üres bin-ek eldobása
stats = stats[stats["osszes"] > 0].copy()

stats["kesedelmes_pct"] = (
    stats["kesedelmes"] / stats["osszes"] * 100
)

# X tengelyhez: bin közepe
stats["amount_mid"] = (
    stats["amount_bin"].astype(float) + BIN_SIZE / 2
)

# --------------------
# Diagram
# --------------------
fig, ax = plt.subplots(figsize=(8,3))

ax.plot(
    stats["amount_mid"],
    stats["kesedelmes_pct"],
    marker="o"
)

ax.set_title(
    "Késedelmes fizetés aránya a számla bruttó összege szerint"
)
ax.set_xlabel("Számla bruttó összege (Ft)")
ax.set_ylabel("Késedelmes fizetés aránya (%)")

# Teljes összeg kiírás az x tengelyen (nincs 1e7)
ax.xaxis.set_major_formatter(
    FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", " "))
)

result = fig
 
```


9. Kérdés: Rajzolj egy vonaldiagramot, ami a késve fizetett számláknál azt mutatja, hogy ha x napig nem fizetett, mekkora valószínűsége hogy x+1-ik napon fizet.    
```python
import warnings; warnings.filterwarnings("ignore")
from matplotlib_theme import apply_default_theme
apply_default_theme()

import matplotlib.pyplot as plt
import pandas as pd

# --------------------
# Paraméterek
# --------------------
MAX_DAYS = 60          # eddig vizsgáljuk: x+1 <= 60
MIN_DELAY_DAYS = 1     # csak késve fizetettek

# --------------------
# Adatelőkészítés
# --------------------
df_tmp = df.copy()

df_tmp["due_in_date"] = pd.to_datetime(df_tmp["due_in_date"], errors="coerce")
df_tmp["clear_date"] = pd.to_datetime(df_tmp["clear_date"], errors="coerce")

df_tmp = df_tmp[
    df_tmp["due_in_date"].notna() &
    df_tmp["clear_date"].notna()
].copy()

df_tmp["delay_days"] = kesedelmes_napok(
    df_tmp["due_in_date"],
    df_tmp["clear_date"])


# csak késve fizetettek (delay >= 1)
df_delayed = df_tmp[df_tmp["delay_days"] >= MIN_DELAY_DAYS].copy()

# --------------------
# Hazard számítás (x nap után -> x+1 napon fizet)
# --------------------
records = []

# x = 0..MAX_DAYS-1 (így x+1 legfeljebb MAX_DAYS)
for x in range(0, MAX_DAYS):
    base = df_delayed[df_delayed["delay_days"] > x]   # még nem fizetett x nap után
    base_n = int(len(base))

    if base_n == 0:
        continue

    paid_next = df_delayed[df_delayed["delay_days"] == (x + 1)]
    m = int(len(paid_next))

    prob_pct = m / base_n * 100

    records.append({
        "Nap": x + 1,  # a "következő nap" (1..MAX_DAYS)
        "Kifizetes_valoszinuseg_pct": float(prob_pct),
        "Bazis_db": base_n
    })

df_plot = pd.DataFrame(records)

# --------------------
# Diagram
# --------------------
fig, ax = plt.subplots(figsize=(8,3))
ax.plot(df_plot["Nap"], df_plot["Kifizetes_valoszinuseg_pct"], marker="o")

ax.set_title("Napi kifizetési valószínűség késés után (hazard rate)")
ax.set_xlabel("Késedelmi nap (x+1)")
ax.set_ylabel("Következő napi kifizetés valószínűsége (%)")

result = fig

```


10. Kérdés: Melyik ügyfélnél nőtt legjobban a fizetési fegyelem 2025-ben 2024-hez képest! Fizettési fegyelem javításán azt értem, hogy változott a késve fizetett számlák aránya. Csak azokat vizsgáld, amelyeknél legalább 10 számla volt mindkét évben!    
```python

import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# --------------------
# Paraméterek
# --------------------
YEAR_1 = 2024
YEAR_2 = 2025
MIN_INVOICES = 10
MIN_DELAY_DAYS = 1   # késedelmes = legalább 1 nap

# --------------------
# Adatelőkészítés
# --------------------
df_tmp = df.copy()

df_tmp["posting_date"] = pd.to_datetime(
    df_tmp["posting_date"], errors="coerce"
)
df_tmp["due_in_date"] = pd.to_datetime(
    df_tmp["due_in_date"], errors="coerce"
)
df_tmp["clear_date"] = pd.to_datetime(
    df_tmp["clear_date"], errors="coerce"
)

df_tmp = df_tmp[
    df_tmp["customer_name"].notna() &
    df_tmp["posting_date"].notna() &
    df_tmp["due_in_date"].notna() &
    df_tmp["clear_date"].notna()
].copy()

df_tmp["Year"] = df_tmp["posting_date"].dt.year

df_tmp["delay_days"] = kesedelmes_napok(
    df_tmp["due_in_date"],
    df_tmp["clear_date"])


df_tmp["delayed"] = df_tmp["delay_days"] >= MIN_DELAY_DAYS

df_tmp = df_tmp[
    df_tmp["Year"].isin([YEAR_1, YEAR_2])
].copy()

# --------------------
# Ügyfél–év statisztika
# --------------------
stats = (
    df_tmp
    .groupby(["customer_name", "Year"])["delayed"]
    .agg(
        invoice_count="count",
        delayed_count="sum"
    )
    .reset_index()
)

# Minimum elemszám feltétel
stats = stats[
    stats["invoice_count"] >= MIN_INVOICES
].copy()

stats["delayed_pct"] = (
    stats["delayed_count"] / stats["invoice_count"] * 100
)

# --------------------
# Év–év összehasonlítás
# --------------------
pivot = (
    stats
    .pivot(
        index="customer_name",
        columns="Year",
        values=["delayed_pct", "invoice_count"]
    )
    .dropna()
)

# Javulás = 2024 arány – 2025 arány
pivot["javulas_pctpont"] = (
    pivot[("delayed_pct", YEAR_1)] -
    pivot[("delayed_pct", YEAR_2)]
)

# --------------------
# LEGJOBB JAVULÁS
# --------------------
best_customer = pivot["javulas_pctpont"].idxmax()
row = pivot.loc[best_customer]

result = {
    "ugyfel": str(best_customer),
    "fizetesi_fegyelem_javulasa_szazalekpont": round(float(row["javulas_pctpont"]), 2),
    f"{YEAR_1}_kesedelmes_arany_pct": round(float(row[("delayed_pct", YEAR_1)]), 2),
    f"{YEAR_2}_kesedelmes_arany_pct": round(float(row[("delayed_pct", YEAR_2)]), 2),
    f"{YEAR_1}_szamlaszam_db": int(row[("invoice_count", YEAR_1)]),
    f"{YEAR_2}_szamlaszam_db": int(row[("invoice_count", YEAR_2)])
}

```


11. Kérdés: 2024-ben hány cégnek lett számla kiállítva?     
```python

import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# Paraméter
YEAR = 2024

df_tmp = df.copy()

# Kiállítás dátumának biztos kezelése
df_tmp["posting_date"] = pd.to_datetime(
    df_tmp["posting_date"], errors="coerce"
)

# Csak 2024-ben kiállított számlák
df_2024 = df_tmp[
    (df_tmp["posting_date"].dt.year == YEAR) &
    (df_tmp["customer_name"].notna())
]

# Egyedi ügyfelek száma
result = int(
    df_2024["customer_name"].nunique()
)


```

12. Kérdés: Mutasd azon a 2023-as számlák számlaszámát és a számlához tartozó vevőt, amelyek legalább 15 napos késedelműek voltak és legalább 6M Ft volt a nettó összeg?      
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# --------------------
# Paraméterek
# --------------------
YEAR = 2023
MIN_DELAY_DAYS = 15
MIN_NET_AMOUNT = 6_000_000

df_tmp = df.copy()

# --------------------
# Dátummezők biztos kezelése
# --------------------
df_tmp["posting_date"] = pd.to_datetime(df_tmp["posting_date"], errors="coerce")
df_tmp["due_in_date"] = pd.to_datetime(df_tmp["due_in_date"], errors="coerce")
df_tmp["clear_date"] = pd.to_datetime(df_tmp["clear_date"], errors="coerce")

# --------------------
# Csak értelmezhető, kifizetett számlák
# --------------------
df_tmp = df_tmp[
    df_tmp["posting_date"].notna() &
    df_tmp["due_in_date"].notna() &
    df_tmp["clear_date"].notna() &
    df_tmp["customer_name"].notna()
].copy()

# --------------------
# Csak 2023-as számlák
# --------------------
df_tmp = df_tmp[
    df_tmp["posting_date"].dt.year == YEAR
].copy()

# --------------------
# Késés napokban
# --------------------
df_tmp["delay_days"] = kesedelmes_napok(
    df_tmp["due_in_date"],
    df_tmp["clear_date"]
)

# --------------------
# Szűrés: késés + nagy összeg
# --------------------
df_filtered = df_tmp[
    (df_tmp["delay_days"] >= MIN_DELAY_DAYS) &
    (df_tmp["Netto"] >= MIN_NET_AMOUNT)
].copy()

# --------------------
# Kimenet (táblázat)
# --------------------
result = (
    df_filtered[
        ["invoice_nr", "customer_name", "Netto", "delay_days"]
    ]
    .sort_values(
        ["delay_days", "Netto"],
        ascending=[False, False]
    )
)

```


13. Kérdés: Mekkora volt a Bomepro nevű ügyfélnek kiállított számla legnagyobb összegű 2024-ben vagy 2025-ben?      
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# --------------------
# Paraméterek
# --------------------
YEARS = [2024, 2025]
QUERY_NAME = "Bomepro"

# --------------------
# Adatelőkészítés
# --------------------
df_tmp = df.copy()

# Dátummező biztos kezelése
df_tmp["posting_date"] = pd.to_datetime(
    df_tmp["posting_date"], errors="coerce"
)

# Csak releváns évek + értelmezhető vevőnév + bruttó összeg
df_tmp = df_tmp[
    df_tmp["posting_date"].dt.year.isin(YEARS) &
    df_tmp["customer_name"].notna() &
    df_tmp["Brutto"].notna()
].copy()

# --------------------
# Entitásfeloldás (KÖTELEZŐ)
# --------------------
candidates = sorted(
    df_tmp["customer_name"].dropna().unique().tolist()
)

resolved_name = resolve_entity(
    query_value=QUERY_NAME,
    candidates=candidates
)

if resolved_name is None:
    result = {
        "message": "Nem található a megadott névhez illeszkedő ügyfél.",
        "keresett_nev": QUERY_NAME,
        "hasonlo_nevek": candidates[:10]
    }
else:
    df_f = df_tmp[
        df_tmp["customer_name"] == resolved_name
    ]

    if len(df_f) == 0:
        result = 0.0
    else:
        result = float(df_f["Brutto"].max())

```

14. Kérdés: Készíts egy táblázatot, ami azokat a 2025-ös számlákat tartalmazza, melyek 15 napon túl lettek kifizetve és legalább 2000000 Ft volt a bruttó összege. A táblázat tartalmazza a számlaszámot, az ügyfél nevét, a kiállítás dátumát, fizetési határidőt és a fizetés dátumát, illetve a bruttó összeget.       
```python
import warnings; warnings.filterwarnings("ignore")
import pandas as pd

# --------------------
# Paraméterek
# --------------------
YEAR = 2025
MIN_DELAY_DAYS = 15
MIN_BRUTTO = 2_000_000

# --------------------
# Adatelőkészítés
# --------------------
df_tmp = df.copy()

df_tmp["posting_date"] = pd.to_datetime(df_tmp["posting_date"], errors="coerce")
df_tmp["due_in_date"] = pd.to_datetime(df_tmp["due_in_date"], errors="coerce")
df_tmp["clear_date"] = pd.to_datetime(df_tmp["clear_date"], errors="coerce")

# Csak értelmezhető, kifizetett számlák
df_tmp = df_tmp[
    df_tmp["posting_date"].notna() &
    df_tmp["due_in_date"].notna() &
    df_tmp["clear_date"].notna() &
    df_tmp["customer_name"].notna() &
    df_tmp["Brutto"].notna()
].copy()

# Csak 2025-ös számlák
df_tmp = df_tmp[
    df_tmp["posting_date"].dt.year == YEAR
].copy()

# --------------------
# Késés napokban
# --------------------
df_tmp["delay_days"] = kesedelmes_napok(
    df_tmp["due_in_date"],
    df_tmp["clear_date"]
)


# --------------------
# Szűrés: késés + nagy összeg
# --------------------
df_filtered = df_tmp[
    (df_tmp["delay_days"] > MIN_DELAY_DAYS) &
    (df_tmp["Brutto"] >= MIN_BRUTTO)
].copy()

# --------------------
# Kimeneti táblázat (RENDEZÉS NÉLKÜL)
# --------------------
result = df_filtered[
    [
        "invoice_nr",
        "customer_name",
        "posting_date",
        "due_in_date",
        "clear_date",
        "Brutto"
    ]
].reset_index(drop=True)

```

15. Kérdés: Rajzolj egy vonadiagramot, ami havi bontásban mutatja azon számlák számát, amik az 10.000.000 Ft feletti összegűek. A vonaldiagramban ne legyen marker.       
```python

import warnings; warnings.filterwarnings("ignore")
from matplotlib_theme import apply_default_theme
apply_default_theme()
import matplotlib.pyplot as plt
import pandas as pd

# --------------------
# Paraméterek
# --------------------
MIN_AMOUNT = 10_000_000  # 10 millió Ft

# --------------------
# Adatelőkészítés
# --------------------
df_tmp = df.copy()

df_tmp["posting_date"] = pd.to_datetime(
    df_tmp["posting_date"], errors="coerce"
)

# Csak értelmezhető dátum és összeg
df_tmp = df_tmp[
    df_tmp["posting_date"].notna() &
    df_tmp["Brutto"].notna()
].copy()

# 10M Ft feletti számlák (abs, visszajárók miatt)
df_tmp["Brutto_abs"] = df_tmp["Brutto"].abs()
df_tmp = df_tmp[
    df_tmp["Brutto_abs"] > MIN_AMOUNT
].copy()

# Havi bontás
df_tmp["Honap"] = df_tmp["posting_date"].dt.to_period("M").dt.to_timestamp()

# --------------------
# Aggregáció
# --------------------
monthly_counts = (
    df_tmp
    .groupby("Honap")
    .size()
    .reset_index(name="Szamlak_szama")
)

# --------------------
# Vonaldiagram (marker nélkül)
# --------------------
fig, ax = plt.subplots(figsize=(8,3))

ax.plot(
    monthly_counts["Honap"],
    monthly_counts["Szamlak_szama"],
    linestyle="-",
    linewidth=1.2
)

ax.set_title("10M Ft feletti számlák száma – havi bontásban")
ax.set_xlabel("Hónap")
ax.set_ylabel("Számlák száma")

result = fig


```

16. Kérdés: Hogy változik annak a valószínűsége, hogy késve lesz kifizetve, annak függvényében, hogy az ügyfél előző, előző 2, előző 3, stb, számlája is késve lett kifizetve. Az eredményt ábrázold egy vonaldiagrammal!       
```python

import warnings; warnings.filterwarnings("ignore")
from matplotlib_theme import apply_default_theme
apply_default_theme()

import matplotlib.pyplot as plt
import pandas as pd

# --------------------
# Paraméterek
# --------------------
MIN_DELAY_DAYS = 1        # késedelmes = legalább 1 nap
MIN_BASE_COUNT = 50       # minimum elemszám a valószínűség számításhoz
MAX_LOOKBACK = 10         # max ennyi egymást követő számlát vizsgálunk

# --------------------
# Adatelőkészítés
# --------------------
df_tmp = df.copy()

df_tmp["posting_date"] = pd.to_datetime(df_tmp["posting_date"], errors="coerce")
df_tmp["due_in_date"] = pd.to_datetime(df_tmp["due_in_date"], errors="coerce")
df_tmp["clear_date"] = pd.to_datetime(df_tmp["clear_date"], errors="coerce")

df_tmp = df_tmp[
    df_tmp["customer_name"].notna() &
    df_tmp["posting_date"].notna() &
    df_tmp["due_in_date"].notna() &
    df_tmp["clear_date"].notna()
].copy()

# Aktuális számla késedelme (kanonikus)
df_tmp["delay_days"] = kesedelmes_napok(
    df_tmp["due_in_date"],
    df_tmp["clear_date"]
)

df_tmp["aktualis_kesedelmes"] = df_tmp["delay_days"] >= MIN_DELAY_DAYS

# --------------------
# Valószínűség számítás
# --------------------
records = []

for x in range(1, MAX_LOOKBACK + 1):

    elozo_kesedelmes_db, elozo_szamlak_db = elozo_kesedelmes_szamlak_szama(
        df=df_tmp,
        customer_id_col="customer_name",
        order_date_col="posting_date",
        due_in_date_col="due_in_date",
        clear_date_col="clear_date",
        x=x,
        y=MIN_DELAY_DAYS
    )

    df_tmp["_elozo_kesedelmes_db"] = elozo_kesedelmes_db
    df_tmp["_elozo_szamlak_db"] = elozo_szamlak_db

    # Csak azok az esetek:
    # - ahol legalább x előző számla volt
    # - mind a x késedelmes volt
    subset = df_tmp[
        (df_tmp["_elozo_szamlak_db"] == x) &
        (df_tmp["_elozo_kesedelmes_db"] == x)
    ]

    base_n = int(len(subset))

    if base_n < MIN_BASE_COUNT:
        break

    delayed_now_n = int(subset["aktualis_kesedelmes"].sum())
    prob_pct = delayed_now_n / base_n * 100

    records.append({
        "elozo_kesedelmes_szamlak_szama": x,
        "valoszinuseg_pct": float(prob_pct),
        "bazis_db": base_n
    })

df_plot = pd.DataFrame(records)

# --------------------
# Diagram
# --------------------
fig, ax = plt.subplots(figsize=(8,3))

ax.plot(
    df_plot["elozo_kesedelmes_szamlak_szama"],
    df_plot["valoszinuseg_pct"],
    marker="o"
)

ax.set_title(
    "Késedelmes fizetés valószínűsége az előző késedelmek számának függvényében"
)

ax.set_xlabel("Egymást követő késedelmes számlák száma")

ax.set_ylabel(
    "Aktuális számla\nkésedelmes fizetésének\nvalószínűsége (%)"
)

ax.set_ylim(bottom=0)

result = fig

```

17. Kérdés: Hogyan változik a késedelmes fizetés aránya a számla összege függvényében?       
```python

import warnings; warnings.filterwarnings("ignore")
from matplotlib_theme import apply_default_theme
apply_default_theme()

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import numpy as np

# --------------------
# Paraméterek
# --------------------
MIN_DELAY_DAYS = 1        # késedelmes = legalább 1 nap
BIN_SIZE = 500_000        # 500 ezer Ft-os sávok
MAX_AMOUNT = 20_000_000   # 20M felett összevonjuk
MIN_BASE_COUNT = 50       # minimum elemszám binenként

# --------------------
# Adatelőkészítés
# --------------------
df_tmp = df.copy()

df_tmp["due_in_date"] = pd.to_datetime(df_tmp["due_in_date"], errors="coerce")
df_tmp["clear_date"] = pd.to_datetime(df_tmp["clear_date"], errors="coerce")

df_tmp = df_tmp[
    df_tmp["Brutto"].notna() &
    df_tmp["due_in_date"].notna() &
    df_tmp["clear_date"].notna()
].copy()

# Késedelem (kanonikus)
df_tmp["delay_days"] = kesedelmes_napok(
    df_tmp["due_in_date"],
    df_tmp["clear_date"]
)

df_tmp["kesedelmes"] = df_tmp["delay_days"] >= MIN_DELAY_DAYS

# Számlaösszeg kezelése
df_tmp["brutto_abs"] = df_tmp["Brutto"].abs()
df_tmp = df_tmp[df_tmp["brutto_abs"] > 0].copy()

df_tmp["brutto_capped"] = df_tmp["brutto_abs"].clip(upper=MAX_AMOUNT)

# --------------------
# Binning
# --------------------
bins = np.arange(0, MAX_AMOUNT + BIN_SIZE, BIN_SIZE)
labels = bins[:-1]

df_tmp["osszeg_bin"] = pd.cut(
    df_tmp["brutto_capped"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

# --------------------
# Statisztika binenként
# --------------------
stats = (
    df_tmp
    .groupby("osszeg_bin")["kesedelmes"]
    .agg(
        osszes="count",
        kesedelmes_db="sum"
    )
    .reset_index()
)

# Csak értelmezhető bin-ek
stats = stats[stats["osszes"] >= MIN_BASE_COUNT].copy()

stats["kesedelmes_pct"] = (
    stats["kesedelmes_db"] / stats["osszes"] * 100
)

# X tengelyhez bin közepe
stats["osszeg_mid"] = (
    stats["osszeg_bin"].astype(float) + BIN_SIZE / 2
)

# --------------------
# Diagram
# --------------------
fig, ax = plt.subplots(figsize=(8,3))

ax.plot(
    stats["osszeg_mid"],
    stats["kesedelmes_pct"],
    marker="o"
)

ax.set_title(
    "Késedelmes fizetés aránya a számla összege szerint"
)

ax.set_xlabel("Számla bruttó összege (Ft)")

ax.set_ylabel(
    "Késedelmes\nszámlák aránya (%)"
)

ax.set_ylim(bottom=0)

ax.xaxis.set_major_formatter(
    FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", " "))
)

result = fig


```