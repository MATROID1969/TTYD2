# engine/data_loader.py

import pandas as pd
from pathlib import Path

# Optional loaders
try:
    import pyreadstat  # for .sav (SPSS)
except ImportError:
    pyreadstat = None


# --------------------------------------------------------
# Loader implementations
# --------------------------------------------------------

def load_csv(path: Path, cfg: dict) -> pd.DataFrame:
    return pd.read_csv(
        path,
        sep=cfg.get("separator", ","),
        encoding=cfg.get("encoding", "utf-8"),
    )


def load_excel(path: Path, cfg: dict) -> pd.DataFrame:
    return pd.read_excel(
        path,
        sheet_name=cfg.get("sheet", 0),
        engine=cfg.get("engine", None),
    )


def load_parquet(path: Path, cfg: dict) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_json(path: Path, cfg: dict) -> pd.DataFrame:
    orient = cfg.get("orient", None)
    return pd.read_json(path, orient=orient)


def load_sav(path: Path, cfg: dict) -> pd.DataFrame:
    if pyreadstat is None:
        raise ImportError("pyreadstat nincs telepítve, nem lehet .sav fájlt olvasni")

    df, meta = pyreadstat.read_sav(path)
    return df


# --------------------------------------------------------
# Loader registry (PLUGIN MAP)
# --------------------------------------------------------

LOADERS = {
    "csv": load_csv,
    "excel": load_excel,
    "xlsx": load_excel,
    "parquet": load_parquet,
    "json": load_json,
    "sav": load_sav,
}


# --------------------------------------------------------
# Public API
# --------------------------------------------------------

def load_data(app_path: str, data_cfg: dict) -> pd.DataFrame:
    """
    Univerzális DataLoader.
    A config.yaml 'data' blokkjából dolgozik.

    Példa:
    data:
      type: excel
      file: transformed.xlsx
    """

    data_type = data_cfg.get("type")
    if not data_type:
        raise ValueError("data.type nincs megadva a config.yaml-ben")

    data_type = data_type.lower()

    if data_type not in LOADERS:
        raise ValueError(
            f"Nem támogatott adat típus: {data_type}. "
            f"Támogatott: {', '.join(LOADERS.keys())}"
        )

    file_name = data_cfg.get("file")
    if not file_name:
        raise ValueError("data.file nincs megadva a config.yaml-ben")

    data_path = Path(app_path) / "data" / file_name

    if not data_path.exists():
        raise FileNotFoundError(f"Adatfájl nem található: {data_path}")

    loader = LOADERS[data_type]
    df = loader(data_path, data_cfg)

    return df
