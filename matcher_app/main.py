"""Точка входу MatcherApp."""
from __future__ import annotations

from matcher.ui_app import MatcherAppUI


def main() -> None:
    app = MatcherAppUI()
    app.run()


if __name__ == "__main__":
    main()
