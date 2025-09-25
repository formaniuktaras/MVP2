"""Пакет MatcherApp."""

from .config import Config, load_config, save_config
from .core import MatcherCore

__all__ = ["Config", "load_config", "save_config", "MatcherCore"]
