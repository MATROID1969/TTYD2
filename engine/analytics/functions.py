#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# =============================================================
# Survivor függvények (változatlan logika)
# =============================================================

import pandas as pd
import numpy as np
import unicodedata
import re
from difflib import SequenceMatcher
from typing import Iterable, Optional, List



def calc_survivor(df_filtered: pd.DataFrame, vegdatum: pd.Timestamp, max_honap: int = 36):
    """
    Gyorsított survivor: suffix-sum a hónap hisztogramokra (O(n + H)).
    S_i = darab, ahol HONAP_KULONBSEG >= i
    A_i = darab, ahol HONAP_TELT_EL    >= i
    Survivor(i) = S_i / A_i
    """
    if df_filtered.empty:
        return pd.DataFrame({"Honap_szam": [], "Survivor": []})

    df = df_filtered.copy()

    start = pd.to_datetime(df["Szerzodeskotes_datuma"], errors="coerce")
    end = pd.to_datetime(df["Kockazatviselés_vege"], errors="coerce")

    mask_valid_start = start.notna() & (start < vegdatum)
    if not mask_valid_start.any():
        return pd.DataFrame({"Honap_szam": [], "Survivor": []})

    start = start[mask_valid_start]
    end = end[mask_valid_start]

    tel = (vegdatum.year - start.dt.year) * 12 + (vegdatum.month - start.dt.month)

    min_veg_vagy_lej = end.where(end.notna() & (end < vegdatum), other=vegdatum)
    dur = (min_veg_vagy_lej.dt.year - start.dt.year) * 12 + (min_veg_vagy_lej.dt.month - start.dt.month)

    tel = tel.clip(lower=0).astype(int).to_numpy()
    dur = dur.clip(lower=0).astype(int).to_numpy()

    if tel.size == 0:
        return pd.DataFrame({"Honap_szam": [], "Survivor": []})
    H = int(min(tel.max(), max_honap))
    if H <= 0:
        return pd.DataFrame({"Honap_szam": [], "Survivor": []})

    tel_c = np.minimum(tel, H + 1)
    dur_c = np.minimum(dur, H + 1)
    bins = H + 2

    cnt_tel = np.bincount(tel_c, minlength=bins)
    cnt_dur = np.bincount(dur_c, minlength=bins)

    at_risk = np.cumsum(cnt_tel[::-1])[::-1]
    survived = np.cumsum(cnt_dur[::-1])[::-1]

    idx = np.arange(1, H + 1)
    A = at_risk[idx]
    S = survived[idx]

    with np.errstate(divide='ignore', invalid='ignore'):
        surv = np.divide(S, A, out=np.zeros_like(S, dtype=float), where=A > 0)

    return pd.DataFrame({"Honap_szam": idx, "Survivor": surv})


def expected_trapezoid(df_surv):
    """Várható élettartam trapezoid integrálással (hónapban)"""
    if df_surv.empty or "Survivor" not in df_surv.columns:
        return 0.0
    return np.trapezoid(df_surv["Survivor"], dx=1)


def conditional_one_year_retention(df_filtered, survivor_df, vegdatum):
    """Kiszámolja, hogy a most aktív szerződések hány százaléka lesz még aktív 1 év múlva."""
    df_tmp = df_filtered.copy()

    df_tmp["Szerzodeskotes_datuma"] = pd.to_datetime(df_tmp["Szerzodeskotes_datuma"], errors="coerce")
    df_tmp["Kockazatviselés_vege"] = pd.to_datetime(df_tmp["Kockazatviselés_vege"], errors="coerce")

    def month_diff(start, end):
        if pd.isna(start) or pd.isna(end):
            return np.nan
        rd = relativedelta(end, start)
        return rd.years * 12 + rd.months

    df_tmp["Eltelt_honap"] = df_tmp["Szerzodeskotes_datuma"].apply(
        lambda d: month_diff(d, vegdatum)
    ).astype("Int64")

    df_tmp = df_tmp[
        (df_tmp["Kockazatviselés_vege"].isna()) |
        (df_tmp["Kockazatviselés_vege"] > vegdatum)
    ]

    surv_lookup = dict(zip(survivor_df["Honap_szam"], survivor_df["Survivor"]))
    cond_probs = []

    for h in df_tmp["Eltelt_honap"].dropna():
        if (h in surv_lookup) and ((h + 12) in surv_lookup):
            cond_probs.append(surv_lookup[h + 12] / surv_lookup[h])
        else:
            cond_probs.append(np.nan)

    return np.nanmean(cond_probs) * 100


def _month_diff_floor(start, end):
    """Egyszerű hónap-különbség relativedelta-val."""
    if pd.isna(start) or pd.isna(end):
        return np.nan
    rd = relativedelta(end, start)
    return rd.years * 12 + rd.months


def compute_lemor_series_by_age(df_in: pd.DataFrame, asof_date: pd.Timestamp, max_honap: int = 36):
    """
    Lemorzsolódás (aktív arány) kor-szeletek szerint az adott vizsgálati dátumra.
    """
    if df_in.empty:
        return pd.DataFrame({"Lag": [], "Aktiv_arany": []})

    df = df_in.copy()
    df["Szerzodeskotes_datuma"] = pd.to_datetime(df["Szerzodeskotes_datuma"], errors="coerce")
    df["Kockazatviselés_vege"] = pd.to_datetime(df["Kockazatviselés_vege"], errors="coerce")

    df = df[df["Szerzodeskotes_datuma"] <= asof_date].copy()
    if df.empty:
        return pd.DataFrame({"Lag": [], "Aktiv_arany": []})

    df["AGE"] = df["Szerzodeskotes_datuma"].apply(
        lambda d: _month_diff_floor(d, asof_date)
    ).astype("Int64")

    is_active_asof = df["Kockazatviselés_vege"].isna() | (df["Kockazatviselés_vege"] >= asof_date)

    rows = []
    for age in range(0, max_honap):
        mask = df["AGE"] == age
        denom = int(mask.sum())
        if denom == 0:
            continue
        num = int((is_active_asof & mask).sum())
        ratio = num / denom if denom > 0 else np.nan
        rows.append({"Lag": -(age + 1), "Aktiv_arany": ratio})

    out = pd.DataFrame(rows).sort_values("Lag")
    return out


def _normalize_and_tokenize(text: str) -> List[str]:
    """
    Normalizálja és tokenizálja a szöveget:
    - kisbetű
    - ékezetek eltávolítása
    - jogi formák eltávolítása
    - szavak listája
    """
    if not isinstance(text, str):
        return []

    text = text.lower()

    # Ékezetek eltávolítása
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Jogi formák eltávolítása
    legal_forms = [
        r"\bkft\b", r"\bbt\b", r"\bzrt\b", r"\bnrt\b",
        r"\bkkt\b", r"\bnyrt\b", r"\bltd\b", r"\binc\b",
        r"\bco\b", r"\bcorp\b", r"\bbeteti\b", r"\btarsasag\b"
    ]
    pattern = r"(" + "|".join(legal_forms) + r")"
    text = re.sub(pattern, "", text)

    # Nem alfanumerikus karakterek szóközzé
    text = re.sub(r"[^a-z0-9]", " ", text)

    # Tokenek
    tokens = re.sub(r"\s+", " ", text).strip().split()

    return tokens


def resolve_entity(
    query_value: str,
    candidates: Iterable[str],
    max_tokens: int = 3,
    min_fuzzy_similarity: float = 0.6
) -> Optional[str]:
    """
    Entitásfeloldás első szó → első szó preferenciával.

    Lépések:
    1) token-alapú szűrés (1..max_tokens)
    2) ha egy marad → vissza
    3) ha több marad → fuzzy döntés
    """

    if not query_value or not candidates:
        return None

    query_tokens = _normalize_and_tokenize(query_value)
    if not query_tokens:
        return None

    # Kandidátumok tokenizálása
    tokenized_candidates = []
    for c in candidates:
        tokens = _normalize_and_tokenize(c)
        if tokens:
            tokenized_candidates.append((c, tokens))

    if not tokenized_candidates:
        return None

    remaining = tokenized_candidates

    # 1️⃣–3️⃣ token szintű szűrés
    for i in range(min(max_tokens, len(query_tokens))):
        matched = [
            (orig, tokens)
            for orig, tokens in remaining
            if len(tokens) > i and tokens[i] == query_tokens[i]
        ]

        if len(matched) == 1:
            return matched[0][0]

        if len(matched) > 1:
            remaining = matched
        else:
            break  # nincs tovább szűkítés

    # Ha egy maradt
    if len(remaining) == 1:
        return remaining[0][0]

    # 4️⃣ Fallback: fuzzy matching
    best_candidate = None
    best_score = 0.0

    query_joined = " ".join(query_tokens)

    for orig, tokens in remaining:
        cand_joined = " ".join(tokens)
        score = SequenceMatcher(None, query_joined, cand_joined).ratio()

        if score > best_score:
            best_score = score
            best_candidate = orig

    if best_score >= min_fuzzy_similarity:
        return best_candidate

    return None


def kesedelmes_napok(
    due_in_date,
    clear_date,
    current_date=None
):
    """
    Vektorizált határidő-eltérés számítás számlákhoz.

    Eredmény (napokban):
    - negatív: határidő előtt fizetett
    - 0: pontosan határidőre vagy hibás (pl. 1900-as) dátum
    - pozitív: késedelmes

    Speciális szabály:
    - ha az eltérés < -180 nap → 0 (adatminőségi korrekció)
    """

    # Biztos dátumkezelés
    due = pd.to_datetime(due_in_date, errors="coerce")
    clear = pd.to_datetime(clear_date, errors="coerce")

    # Referencia dátum nem fizetett számlákhoz
    if current_date is None:
        ref = pd.Timestamp.today().normalize()
    else:
        ref = pd.to_datetime(current_date)

    # ahol nincs clear_date → aktuális dátum
    effective_clear = clear.fillna(ref)

    # nap eltérés
    day_diff = (effective_clear - due).dt.days

    # NaN → 0
    day_diff = day_diff.fillna(0)

    # 1900-as / extrém korai dátumok kiszűrése
    day_diff = day_diff.where(day_diff >= -180, 0)

    return day_diff.astype(int)


def fizetesi_hossz(
    posting_date,
    due_in_date
):
    """
    Vektorizált fizetési határidő hossz számítás számlákhoz.

    Eredmény (napokban):
    - pozitív: ennyi napos fizetési határidő
    - 0: azonnali fizetés vagy hibás adat
    - negatív eredmény nem engedélyezett (0-ra korrigálva)
    """

    # Biztos dátumkezelés
    post = pd.to_datetime(posting_date, errors="coerce")
    due = pd.to_datetime(due_in_date, errors="coerce")

    # nap különbség
    day_diff = (due - post).dt.days

    # NaN → 0
    day_diff = day_diff.fillna(0)

    # negatív értékek → 0
    day_diff = day_diff.clip(lower=0)

    return day_diff.astype(int)

def elozo_kesedelmes_szamlak_szama(
    df,
    customer_id_col,
    order_date_col,
    due_in_date_col,
    clear_date_col,
    x,
    y
):
    """
    Ügyfelenként kiszámolja, hogy az aktuális számlát megelőző
    x darab számla közül:
    - hány volt legalább y nap késedelmes
    - hány előző számla létezett összesen
    """

    df = df.copy()

    # Időrendi rendezés ügyfelenként
    df = df.sort_values([customer_id_col, order_date_col])

    # Késedelem számítása (kanonikus függvény)
    df["_kesedelem_nap"] = kesedelmes_napok(
        df[due_in_date_col],
        df[clear_date_col]
    )

    # késedelmes-e (bool)
    df["_kesedelmes"] = df["_kesedelem_nap"] >= y

    # 1️⃣ Előző késedelmes számlák száma
    elozo_kesedelmes_db = (
        df
        .groupby(customer_id_col)["_kesedelmes"]
        .apply(
            lambda s: (
                s.shift(1)
                 .rolling(window=x, min_periods=1)
                 .sum()
            )
        )
        .reset_index(level=0, drop=True)   # 🔑 KRITIKUS SOR
        .fillna(0)
        .astype(int)
    )

    # 2️⃣ Előző számlák száma összesen
    elozo_szamlak_db = (
        df
        .groupby(customer_id_col)
        .cumcount()
        .clip(upper=x)
        .astype(int)
    )

    return elozo_kesedelmes_db, elozo_szamlak_db

