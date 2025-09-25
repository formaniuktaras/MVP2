"""Модуль нормалізації полів для MatcherApp."""
from __future__ import annotations

import re
import unicodedata
from typing import Dict

import pandas as pd

_ALLOWED_CHARS_RE = re.compile(r"[^a-z0-9+\.\- ]+")
_MULTI_SPACE_RE = re.compile(r"\s+")

_CYR_TO_LAT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "є": "ie",
    "ж": "zh",
    "з": "z",
    "и": "y",
    "і": "i",
    "ї": "i",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ь": "",
    "ю": "iu",
    "я": "ia",
    "ы": "y",
    "э": "e",
}


def _simplify_text(value: str) -> str:
    """Зводить рядок до базового латинського набору символів."""
    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    converted = []
    for char in value:
        if char in _CYR_TO_LAT:
            converted.append(_CYR_TO_LAT[char])
        else:
            converted.append(char)
    simplified = "".join(converted)
    simplified = _MULTI_SPACE_RE.sub(" ", simplified)
    simplified = _ALLOWED_CHARS_RE.sub(" ", simplified)
    return simplified.strip()


def normalize_text(value: object) -> str:
    """Повертає нормалізований текст для загальних полів."""
    if value is None:
        return ""
    text = str(value)
    if not text.strip():
        return ""
    return _simplify_text(text)


def normalize_film_type(value: object, film_map: Dict[str, str]) -> str:
    """Нормалізує тип плівки з урахуванням словника."""
    base = normalize_text(value)
    if not base:
        return ""
    key = base.replace("  ", " ")
    mapped = film_map.get(key)
    if mapped:
        return mapped
    return film_map.get(key.replace(" ", ""), base) or base


def build_block_key(brand: str, model: str, film_type: str) -> str:
    """Формує blocking-ключ."""
    return " | ".join(part for part in (brand, model, film_type) if part)


def normalize_dataframe(df: pd.DataFrame, film_map: Dict[str, str]) -> pd.DataFrame:
    """Повертає копію DataFrame з нормалізованими колонками."""
    required_columns = ["brand", "model", "film_type"]
    for column in required_columns:
        if column not in df.columns:
            df[column] = ""
    df = df.copy()
    df["brand_norm"] = df["brand"].map(normalize_text)
    df["model_norm"] = df["model"].map(normalize_text)
    df["film_type_norm"] = df["film_type"].map(lambda val: normalize_film_type(val, film_map))
    df["block_key"] = df.apply(
        lambda row: build_block_key(row.get("brand_norm", ""), row.get("model_norm", ""), row.get("film_type_norm", "")),
        axis=1,
    )
    return df
