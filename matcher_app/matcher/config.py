"""Конфігурація застосунку MatcherApp."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import json

CONFIG_FILE_NAME = "config.json"


@dataclass
class Config:
    """Структура конфігурації matcher-ядра."""

    exact_threshold: int = 85
    near_threshold: int = 70
    weights: Dict[str, int] = field(
        default_factory=lambda: {
            "brand_exact": 40,
            "model_fuzzy": 35,
            "film_exact": 15,
            "name_fuzzy": 5,
            "price_proximity": 5,
        }
    )
    price_delta: float = 0.10
    film_map: Dict[str, str] = field(
        default_factory=lambda: {
            "матова": "матова",
            "matte": "матова",
            "anti glare": "матова",
            "anti-glare": "матова",
            "прозора": "прозора",
            "clear": "прозора",
            "privacy matte": "privacy matte",
            "privacy mate": "privacy mate",
            "privacy clear": "privacy clear",
            "anti blue": "anti-blue",
            "anti-blue": "anti-blue",
        }
    )
    last_mappings: Dict[str, Dict[str, str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Створює конфігурацію з dict, насичуючи дефолтні значення."""
        cfg = cls()
        cfg.exact_threshold = int(data.get("exact_threshold", cfg.exact_threshold))
        cfg.near_threshold = int(data.get("near_threshold", cfg.near_threshold))
        cfg.price_delta = float(data.get("price_delta", cfg.price_delta))
        cfg.weights.update(data.get("weights", {}))
        cfg.film_map.update({k.lower(): v for k, v in data.get("film_map", {}).items()})
        cfg.last_mappings.update(data.get("last_mappings", {}))
        return cfg

    def to_dict(self) -> Dict[str, Any]:
        """Серіалізує конфігурацію у dict."""
        return {
            "exact_threshold": self.exact_threshold,
            "near_threshold": self.near_threshold,
            "price_delta": self.price_delta,
            "weights": self.weights,
            "film_map": self.film_map,
            "last_mappings": self.last_mappings,
        }


def get_config_path(base_dir: Optional[Path] = None) -> Path:
    """Повертає шлях до файлу конфігурації біля exe/скрипту."""
    if base_dir is None:
        base_dir = Path.cwd()
    return base_dir / CONFIG_FILE_NAME


def load_config(base_dir: Optional[Path] = None) -> Config:
    """Завантажує конфігурацію з JSON, якщо файл існує."""
    cfg = Config()
    cfg_path = get_config_path(base_dir)
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg = Config.from_dict(data)
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"Не вдалося прочитати конфіг: {exc}") from exc
    return cfg


def save_config(cfg: Config, base_dir: Optional[Path] = None) -> None:
    """Зберігає конфігурацію у JSON."""
    cfg_path = get_config_path(base_dir)
    try:
        cfg_path.write_text(json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Не вдалося зберегти конфіг: {exc}") from exc
