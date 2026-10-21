"""Centralized structured logging factory."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path

import yaml

_CONFIGURED = False


def setup_logging(config_path: str | Path | None = None) -> None:
    """Configure root logging from ``config/logging.yaml`` (idempotent).

    Falls back to a basic INFO console handler when the YAML file
    is missing so CLI tooling never crashes on logging setup.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return
    default = Path(__file__).resolve().parents[1] / "config" / "logging.yaml"
    path = Path(config_path) if config_path else default
    try:
        with open(path, encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
        log_file = cfg["handlers"]["file"]["filename"]
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logging.config.dictConfig(cfg)
    except FileNotFoundError:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger, ensuring logging is configured first."""
    setup_logging()
    return logging.getLogger(name)
