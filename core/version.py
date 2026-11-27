"""Application version and GitHub release metadata."""

from __future__ import annotations

import re
from typing import Tuple

APP_NAME = "PDF整理工具"
APP_VERSION = "1.1.0"
GITHUB_REPO = "AeNzs/PDFKit"
INSTALLER_ASSET_HINT = "setup.exe"


def normalize_version(version_str: str) -> str:
    """Strip leading 'v'/'V' and whitespace from a version string."""
    cleaned = str(version_str or "").strip()
    if cleaned.lower().startswith("v"):
        cleaned = cleaned[1:]
    return cleaned


def parse_version(version_str: str) -> Tuple[int, ...]:
    """Extract numeric version tuple (e.g. 'v1.2.10-beta' -> (1, 2, 10))."""
    cleaned = normalize_version(version_str)
    parts = re.findall(r"\d+", cleaned)
    if not parts:
        return (0,)
    return tuple(int(p) for p in parts)


def is_newer_version(remote_version: str, current_version: str = APP_VERSION) -> bool:
    """Return True if remote_version is strictly newer than current_version."""
    remote = parse_version(remote_version)
    current = parse_version(current_version)
    max_len = max(len(remote), len(current))
    remote_padded = remote + (0,) * (max_len - len(remote))
    current_padded = current + (0,) * (max_len - len(current))
    return remote_padded > current_padded
