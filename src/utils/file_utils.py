"""Filesystem helpers: directories, archiving, timestamped names."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    """Create a directory (parents included) and return it as :class:`Path`."""
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def timestamp(fmt: str = "%Y%m%d_%H%M%S") -> str:
    """Return the current local timestamp formatted for filenames."""
    return datetime.now().strftime(fmt)


def archive_file(src: str | Path, archive_dir: str | Path) -> Path:
    """Copy ``src`` into ``archive_dir`` with a timestamp suffix.

    Args:
        src: File to archive.
        archive_dir: Destination directory (created if missing).

    Returns:
        Path of the archived copy.
    """
    src_path = Path(src)
    dest_dir = ensure_dir(archive_dir)
    dest = dest_dir / f"{src_path.stem}_{timestamp()}{src_path.suffix}"
    shutil.copy2(src_path, dest)
    return dest
