"""Бізнес-логіка MatcherApp."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from . import config as config_module
from .hashid import hashid
from .io_utils import apply_mapping, detect_columns, read_table
from .matching import match_user_vs_suppliers
from .models import ColumnMapping, SupplierData
from .normalization import normalize_dataframe


class MatcherCore:
    """Диригент бізнес-логіки: імпорт, нормалізація, матчинг."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = Path(base_dir or Path.cwd())
        self.config = config_module.load_config(self.base_dir)
        self.logger = None
        self.user_df: Optional[pd.DataFrame] = None
        self.user_path: Optional[Path] = None
        self.suppliers: List[SupplierData] = []
        self.results: Dict[str, pd.DataFrame] | None = None

    def attach_logger(self, logger) -> None:
        """Присвоює створений logger (для ін'єкції з UI)."""
        self.logger = logger

    # --- Конфіг та мапінг ---
    def load_dataframe(self, path: Path) -> pd.DataFrame:
        """Зчитує таблицю у DataFrame."""
        df = read_table(path)
        if df.empty:
            raise ValueError("Файл не містить даних")
        return df

    def suggest_mapping(self, key: str, df: pd.DataFrame) -> ColumnMapping:
        """Повертає пропонований мапінг колонок."""
        last = self.config.last_mappings.get(key, {})
        mapping = detect_columns(df, last_mapping=last)
        return mapping

    def update_mapping_cache(self, key: str, mapping: ColumnMapping) -> None:
        """Зберігає мапінг у конфіг для подальшого використання."""
        self.config.last_mappings[key] = mapping.to_dict()
        config_module.save_config(self.config, self.base_dir)

    # --- Робота з даними ---
    def set_user_price(self, path: Path, df: pd.DataFrame, mapping: ColumnMapping) -> None:
        """Зберігає мій прайс."""
        prepared = apply_mapping(df, mapping)
        normalized = normalize_dataframe(prepared, self.config.film_map)
        self.user_df = normalized
        self.user_path = path
        self.update_mapping_cache("user", mapping)
        self._log_info(f"Завантажено мій прайс: {path} ({len(normalized)} рядків)")

    def add_supplier(self, path: Path, df: pd.DataFrame, mapping: ColumnMapping) -> None:
        """Додає прайс постачальника."""
        prepared = apply_mapping(df, mapping)
        normalized = normalize_dataframe(prepared, self.config.film_map)
        supplier = SupplierData(path=path, dataframe=normalized, mapping=mapping)
        self.suppliers.append(supplier)
        cache_key = f"supplier::{path.suffix.lower()}"
        self.update_mapping_cache(cache_key, mapping)
        self._log_info(f"Додано постачальника: {path.name} ({len(normalized)} рядків)")

    def clear_suppliers(self) -> None:
        self.suppliers.clear()

    # --- Матчинг ---
    def run_matching(self, generate_canon_id: bool = False) -> Dict[str, pd.DataFrame]:
        """Виконує процедуру матчінгу."""
        if self.user_df is None:
            raise ValueError("Спочатку завантажте мій прайс")
        if not self.suppliers:
            raise ValueError("Додайте хоча б один прайс постачальника")
        supplier_payload: List[tuple[str, pd.DataFrame]] = []
        for supplier in self.suppliers:
            supplier_payload.append((supplier.source_name, supplier.dataframe))
        results = match_user_vs_suppliers(self.user_df, supplier_payload, self.config)
        if generate_canon_id:
            for key, df in results.items():
                if df.empty:
                    continue
                df["canon_id"] = df.apply(
                    lambda row: hashid(
                        str(row.get("brand_norm", "")),
                        str(row.get("model_norm", "")),
                        str(row.get("film_type_norm", "")),
                    ),
                    axis=1,
                )
        self.results = results
        counts = {key: len(df) for key, df in results.items()}
        self._log_info(f"Матчинг завершено: {counts}")
        return results

    # --- Сервісні ---
    def stats_summary(self) -> str:
        if not self.results:
            return "Матчинг ще не виконувався"
        exact = len(self.results.get("exact", []))
        near = len(self.results.get("near", []))
        unmatched = len(self.results.get("unmatched", []))
        return f"Exact: {exact} | Near: {near} | Unmatched: {unmatched}"

    def _log_info(self, message: str) -> None:
        if self.logger:
            self.logger.info(message)

    def _log_error(self, message: str) -> None:
        if self.logger:
            self.logger.error(message)
