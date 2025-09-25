"""Модуль матчінгу між прайсами."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
from rapidfuzz import fuzz

from .config import Config


def _to_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def score_row(user_row: Dict[str, object], supplier_row: Dict[str, object], cfg: Config) -> float:
    """Розраховує комбінований бал для рядка користувача та кандидата."""
    score = 0.0
    weights = cfg.weights
    if user_row.get("brand_norm") and user_row.get("brand_norm") == supplier_row.get("brand_norm"):
        score += weights.get("brand_exact", 0)
    model_user = user_row.get("model_norm", "")
    model_supplier = supplier_row.get("model_norm", "")
    if model_user and model_supplier:
        ratio = fuzz.token_set_ratio(model_user, model_supplier)
        score += ratio / 100.0 * weights.get("model_fuzzy", 0)
    film_user = user_row.get("film_type_norm", "")
    film_supplier = supplier_row.get("film_type_norm", "")
    if film_user and film_supplier and film_user == film_supplier:
        score += weights.get("film_exact", 0)
    name_user = user_row.get("name", "")
    name_supplier = supplier_row.get("name", "")
    if name_user and name_supplier:
        partial = fuzz.partial_ratio(str(name_user), str(name_supplier))
        score += partial / 100.0 * weights.get("name_fuzzy", 0)
    price_user = _to_float(user_row.get("price"))
    price_supplier = _to_float(supplier_row.get("price"))
    if price_user and price_supplier and price_user > 0:
        delta = abs(price_user - price_supplier) / price_user
        if delta <= cfg.price_delta:
            score += weights.get("price_proximity", 0)
    return min(score, 100.0)


@dataclass
class MatchResult:
    exact: pd.DataFrame
    near: pd.DataFrame
    unmatched: pd.DataFrame


def match_user_vs_suppliers(
    user_df: pd.DataFrame, suppliers: List[tuple[str, pd.DataFrame]], cfg: Config
) -> Dict[str, pd.DataFrame]:
    """Виконує strict та fuzzy матчинг між користувацьким прайсом та постачальниками."""
    if user_df.empty:
        raise ValueError("Мій прайс порожній")
    if not suppliers:
        raise ValueError("Додайте хоча б один прайс постачальника")
    user_work = user_df.reset_index(drop=True).copy()
    user_work["__user_idx"] = user_work.index

    supplier_frames: List[pd.DataFrame] = []
    for source_name, df in suppliers:
        if df.empty:
            continue
        supplier_copy = df.copy()
        supplier_copy["__source__"] = source_name
        supplier_copy["__supplier_idx"] = supplier_copy.index
        supplier_frames.append(supplier_copy)
    if not supplier_frames:
        raise ValueError("Усі прайси постачальників порожні")
    suppliers_df = pd.concat(supplier_frames, ignore_index=True)
    rename_map = {
        col: f"{col}_sup"
        for col in suppliers_df.columns
        if col not in {"block_key", "__source__", "__supplier_idx"}
    }
    suppliers_df = suppliers_df.rename(columns=rename_map)

    merged = user_work.merge(
        suppliers_df,
        on="block_key",
        how="left",
    )
    exact_mask = merged["__source__"].notna()
    exact_df = merged.loc[exact_mask].copy()
    exact_df["score"] = 100.0

    matched_user_ids = set(exact_df["__user_idx"].tolist())
    unmatched_users = user_work[~user_work["__user_idx"].isin(matched_user_ids)].copy()

    near_rows = []
    unmatched_rows = []

    suppliers_grouped = suppliers_df.groupby(["brand_norm_sup", "film_type_norm_sup"])

    for _, user_row in unmatched_users.iterrows():
        key = (user_row.get("brand_norm"), user_row.get("film_type_norm"))
        try:
            candidates = suppliers_grouped.get_group(key)
        except KeyError:
            unmatched_rows.append(user_row)
            continue
        best_score = 0.0
        best_candidate = None
        for _, supplier_row in candidates.iterrows():
            score = score_row(user_row.to_dict(), supplier_row.to_dict(), cfg)
            if score > best_score:
                best_score = score
                best_candidate = supplier_row
        if best_candidate is None or best_score < cfg.near_threshold:
            unmatched_rows.append(user_row)
            continue
        result_row = user_row.to_dict()
        for column, value in best_candidate.items():
            result_row[column] = value
        result_row["score"] = best_score
        result_row["auto_match"] = best_score >= cfg.exact_threshold
        near_rows.append(result_row)

    near_df = pd.DataFrame(near_rows)
    unmatched_df = pd.DataFrame(unmatched_rows)

    return {
        "exact": exact_df,
        "near": near_df,
        "unmatched": unmatched_df,
    }
