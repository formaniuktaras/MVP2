"""Дата-класи для опису мапінгів та джерел даних MatcherApp."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class ColumnMapping:
    """Відображення логічних полів на фактичні назви колонок."""

    name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    film_type: Optional[str] = None
    sku: Optional[str] = None
    product_id: Optional[str] = None
    price: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Повертає словник для серіалізації."""
        return {
            "name": self.name,
            "brand": self.brand,
            "model": self.model,
            "film_type": self.film_type,
            "sku": self.sku,
            "product_id": self.product_id,
            "price": self.price,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Optional[str]]) -> "ColumnMapping":
        """Створює ColumnMapping з dict."""
        return cls(
            name=data.get("name"),
            brand=data.get("brand"),
            model=data.get("model"),
            film_type=data.get("film_type"),
            sku=data.get("sku"),
            product_id=data.get("product_id"),
            price=data.get("price"),
        )

    def required_missing(self) -> list[str]:
        """Повертає список відсутніх обов'язкових полів."""
        missing = []
        for attr in ("name", "brand", "model", "film_type"):
            if getattr(self, attr) in (None, ""):
                missing.append(attr)
        return missing


@dataclass
class SupplierData:
    """Прайс постачальника та його атрибути."""

    path: Path
    dataframe: "pd.DataFrame"
    mapping: ColumnMapping = field(default_factory=ColumnMapping)

    @property
    def source_name(self) -> str:
        """Назва джерела (файл)."""
        return self.path.name
