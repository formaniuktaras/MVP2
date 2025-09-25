"""Експорт результатів матчінгу у CSV."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

CSV_PARAMS = {"index": False, "encoding": "utf-8-sig", "sep": ","}


def export_csv(df: pd.DataFrame, path: Path | str, columns: Optional[Iterable[str]] = None) -> None:
    """Зберігає DataFrame у CSV з utf-8-sig."""
    target = Path(path)
    if df.empty:
        # Створюємо порожній файл з заголовком для прозорості.
        if columns is None:
            df.head(0).to_csv(target, **CSV_PARAMS)
        else:
            pd.DataFrame(columns=list(columns)).to_csv(target, **CSV_PARAMS)
        return
    export_df = df
    if columns:
        available = [col for col in columns if col in df.columns]
        export_df = df[available]
    export_df.to_csv(target, **CSV_PARAMS)


def export_exact(df: pd.DataFrame, path: Path | str) -> None:
    columns = [
        "name",
        "brand",
        "model",
        "film_type",
        "sku",
        "id",
        "price",
        "block_key",
        "__source__",
        "name_sup",
        "brand_sup",
        "model_sup",
        "film_type_sup",
        "price_sup",
        "score",
    ]
    export_csv(df, path, columns)


def export_near(df: pd.DataFrame, path: Path | str) -> None:
    columns = [
        "name",
        "brand",
        "model",
        "film_type",
        "price",
        "block_key",
        "score",
        "auto_match",
        "__source__",
        "name_sup",
        "brand_sup",
        "model_sup",
        "film_type_sup",
        "price_sup",
    ]
    export_csv(df, path, columns)


def export_unmatched(df: pd.DataFrame, path: Path | str) -> None:
    columns = ["name", "brand", "model", "film_type", "sku", "id", "price", "block_key"]
    export_csv(df, path, columns)
