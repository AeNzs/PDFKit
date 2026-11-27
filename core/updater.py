"""GitHub Releases auto-update checker and installer downloader (stdlib only)."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

from core.version import (
    APP_VERSION,
    GITHUB_REPO,
    INSTALLER_ASSET_HINT,
    is_newer_version,
    normalize_version,
)


class UpdateCheckError(Exception):
    """Raised when checking GitHub Releases fails."""


class NoReleasePublishedError(UpdateCheckError):
    """Raised when the repository has no published releases yet (HTTP 404)."""


class DownloadCancelledError(Exception):
    """Raised when the user cancels an active update download."""


@dataclass
class ReleaseInfo:
    version: str
    tag_name: str
    title: str
    notes: str
    html_url: str
    download_url: Optional[str]
    asset_name: str
    asset_size: int
    has_update: bool


def _pick_installer_asset(assets: list) -> tuple[Optional[str], str, int]:
    """Select the best Windows installer .exe asset from a GitHub Release."""
    fallback_exe = None
    for asset in assets:
        name = str(asset.get("name", ""))
        url = asset.get("browser_download_url")
        size = int(asset.get("size", 0) or 0)
        if not url:
            continue
        lower = name.lower()
        if lower.endswith(INSTALLER_ASSET_HINT):
            return url, name, size
        if lower.endswith(".exe") and fallback_exe is None:
            fallback_exe = (url, name, size)

    if fallback_exe is not None:
        return fallback_exe
    return None, "", 0


def fetch_latest_release(
    repo: str = GITHUB_REPO,
    current_version: str = APP_VERSION,
    timeout: float = 10.0,
) -> ReleaseInfo:
    """Query GitHub Releases API for the latest published release."""
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"PDFOrganizeTool/{current_version}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise NoReleasePublishedError("No published release found on GitHub.") from exc
        raise UpdateCheckError(f"GitHub API HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise UpdateCheckError(f"Network error: {exc.reason}") from exc
    except Exception as exc:
        raise UpdateCheckError(str(exc)) from exc

    tag_name = str(payload.get("tag_name", "")).strip()
    version = normalize_version(tag_name)
    title = str(payload.get("name") or tag_name or version).strip()
    notes = str(payload.get("body") or "").strip()
    html_url = str(
        payload.get("html_url") or f"https://github.com/{repo}/releases"
    ).strip()

    download_url, asset_name, asset_size = _pick_installer_asset(
        payload.get("assets") or []
    )
    has_update = is_newer_version(tag_name, current_version)

    return ReleaseInfo(
        version=version,
        tag_name=tag_name,
        title=title,
        notes=notes,
        html_url=html_url,
        download_url=download_url,
        asset_name=asset_name,
        asset_size=asset_size,
        has_update=has_update,
    )


def download_installer(
    url: str,
    filename: str,
    on_progress: Optional[Callable[[int, int], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
    timeout: float = 30.0,
) -> str:
    """Stream installer .exe into a temp update folder and return its local path."""
    update_dir = os.path.join(tempfile.gettempdir(), "PDFOrganizeTool_update")
    os.makedirs(update_dir, exist_ok=True)

    safe_name = os.path.basename(filename) or "PDFOrganizeTool_Setup.exe"
    target_path = os.path.join(update_dir, safe_name)
    part_path = target_path + ".part"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"PDFOrganizeTool/{APP_VERSION}"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total_size = int(resp.headers.get("Content-Length", 0) or 0)
            downloaded = 0
            chunk_size = 64 * 1024

            with open(part_path, "wb") as out_file:
                while True:
                    if is_cancelled and is_cancelled():
                        raise DownloadCancelledError("Download cancelled by user.")
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if on_progress:
                        on_progress(downloaded, total_size)

        if os.path.exists(target_path):
            os.remove(target_path)
        os.replace(part_path, target_path)
        return target_path
    except Exception:
        if os.path.exists(part_path):
            try:
                os.remove(part_path)
            except OSError:
                pass
        raise


def launch_installer_for_update(installer_path: str) -> None:
    """Launch Inno Setup installer silently to close, update, and restart the app."""
    if not os.path.isfile(installer_path):
        raise FileNotFoundError(f"Installer file not found: {installer_path}")

    cmd = [
        installer_path,
        "/SILENT",
        "/SP-",
        "/CLOSEAPPLICATIONS",
        "/RESTARTAPPLICATIONS",
    ]
    creation_flags = 0
    if os.name == "nt":
        creation_flags = (
            getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
    subprocess.Popen(cmd, creationflags=creation_flags, close_fds=True)
