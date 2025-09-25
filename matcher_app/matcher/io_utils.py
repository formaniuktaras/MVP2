"""Інструменти введення/виведення для MatcherApp."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

from .models import ColumnMapping

_REQUIRED_FIELDS = ("name", "brand", "model", "film_type")

_COLUMN_ALIASES: Dict[str, Iterable[str]] = {
    "name": [
        "назва позиції",
        "назва",
        "title",
        "name",
        "productname",
        "наименование",
    ],
    "brand": [
        "виробник",
        "бренд",
        "brand",
        "бренд пристрою",
        "производитель",
    ],
    "model": [
        "модель",
        "model",
        "модель ",
        "модель устройства",
        "device model",
    ],
    "film_type": [
        "тип_плівки",
        "тип плівки",
        "film_type",
        "серія чохла",
        "тип",
        "series",
        "лінійка",
    ],
    "sku": [
        "код_товару",
        "sku",
        "артикул",
        "код товару",
        "vendorcode",
    ],
    "product_id": [
        "ідентифікатор_товару",
        "id",
        "ідентифікатор товару",
    ],
    "price": [
        "ціна",
        "price",
        "цена",
    ],
}


def _normalize_column_name(name: str) -> str:
    return name.strip().lower().replace("\u00a0", " ")


def read_table(path: Path) -> pd.DataFrame:
    """Зчитує CSV/XLSX у DataFrame."""
    if not path.exists():
        raise FileNotFoundError(f"Файл не знайдено: {path}")
    if path.suffix.lower() in {".csv", ".txt"}:
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError("Підтримуються лише CSV або XLSX")


def detect_columns(df: pd.DataFrame, last_mapping: Optional[Dict[str, str]] = None) -> ColumnMapping:
    """Пробує знайти відповідність колонок у DataFrame."""
    mapping = ColumnMapping()
    normalized = {_normalize_column_name(col): col for col in df.columns}
    if last_mapping:
        for field, column in last_mapping.items():
            if column and column in df.columns:
                setattr(mapping, field, column)
    for field, aliases in _COLUMN_ALIASES.items():
        if getattr(mapping, field):
            continue
        for alias in aliases:
            alias_norm = _normalize_column_name(alias)
            for candidate_norm, original in normalized.items():
                if candidate_norm == alias_norm:
                    setattr(mapping, field, original)
                    break
            if getattr(mapping, field):
                break
    return mapping


def apply_mapping(df: pd.DataFrame, mapping: ColumnMapping) -> pd.DataFrame:
    """Повертає DataFrame з уніфікованими колонками."""
    missing = mapping.required_missing()
    if missing:
        raise ValueError(f"Вкажіть колонки для: {', '.join(missing)}")
    rename_map = {
        mapping.name: "name",
        mapping.brand: "brand",
        mapping.model: "model",
        mapping.film_type: "film_type",
    }
    optional_fields = {
        mapping.sku: "sku",
        mapping.product_id: "id",
        mapping.price: "price",
    }
    for src, dst in optional_fields.items():
        if src:
            rename_map[src] = dst
    df = df.rename(columns=rename_map)
    # Забезпечимо наявність опційних колонок
    for optional in ("sku", "id", "price"):
        if optional not in df.columns:
            df[optional] = None
    return df
