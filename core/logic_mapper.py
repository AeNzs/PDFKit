"""Module 04 engine: Mapping by Logic (Alias Table + Regex + Multi-source Copy/Move)."""

from __future__ import annotations

import json
import os
import re
import shutil
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.pdf_sign import get_app_dir, safe_filename


def get_logic_config_path() -> str:
    """Return writable logic_mapper_rules.json path in per-user AppData."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        cfg_dir = os.path.join(appdata, "PDF整理工具")
        os.makedirs(cfg_dir, exist_ok=True)
        return os.path.join(cfg_dir, "logic_mapper_rules.json")
    return os.path.join(get_app_dir(), "logic_mapper_rules.json")


DEFAULT_LOGIC_CONFIG_PATH = get_logic_config_path()

DEFAULT_WORK_MODE = "create_from_files"  # "create_from_files" | "existing_folders"
DEFAULT_MONTH_LABEL = "10月"
DEFAULT_FOLDER_TEMPLATE = "PJI-{PT}-{BULAN}物资结算开票资料"
DEFAULT_FILE_FALLBACK_REGEX = r"PO-([A-Za-z0-9]+)-"
DEFAULT_IGNORE_KEYS = "PJI"

DEFAULT_TARGET_REGEX = r"PJI-([A-Za-z0-9]+)-"
DEFAULT_TARGET_SCAN = "folder"  # "folder" | "files" | "both"

DEFAULT_ALIAS_RULES: List[Dict[str, Any]] = [
    {"enabled": True, "match_code": "AMI", "pt_name": "AMI", "month_override": ""},
    {"enabled": True, "match_code": "ANI", "pt_name": "ANI", "month_override": ""},
    {"enabled": True, "match_code": "BMSI", "pt_name": "BMSI", "month_override": ""},
    {"enabled": True, "match_code": "BSE", "pt_name": "BSE", "month_override": ""},
    {"enabled": True, "match_code": "CMI", "pt_name": "CMI", "month_override": ""},
    {"enabled": True, "match_code": "PII", "pt_name": "PII", "month_override": ""},
    {"enabled": True, "match_code": "PJI-MXZ-26001", "pt_name": "TEK", "month_override": "{BULAN}中国船"},
    {"enabled": True, "match_code": "PJI-MXZ-26002", "pt_name": "XGIM", "month_override": "{BULAN}中国船"},
    {"enabled": True, "match_code": "PJI-MXZ-26207", "pt_name": "IPM", "month_override": "{BULAN}中国船"},
    {"enabled": True, "match_code": "PJI-MXZ-26320", "pt_name": "PAI", "month_override": "{BULAN}中国船"},
]

DEFAULT_SOURCE_RULES: List[Dict[str, Any]] = [
    {
        "enabled": True,
        "name": "框架协议 (Konsinyasi)",
        "source_dir": r"\\10.50.2.18\【重要文件】pji结算\PJI-框架协议",
        "action": "copy",
        "match_mode": "token",
        "file_pattern": "",
        "include_subfolders": False,
        "conflict": "skip",
    },
    {
        "enabled": True,
        "name": "税卡 (NPWP)",
        "source_dir": r"\\10.50.2.18\【重要文件】pji结算\PJI-税卡",
        "action": "copy",
        "match_mode": "token",
        "file_pattern": "",
        "include_subfolders": False,
        "conflict": "skip",
    },
]

IGNORED_SYSTEM_FILES = {"desktop.ini", "thumbs.db", ".ds_store"}


@dataclass
class LogicMatchEntry:
    folder_name: str
    folder_path: str
    key: str
    rule_name: str
    action: str  # "copy" | "move" | "-"
    conflict: str  # "skip" | "overwrite"
    source_path: str
    file_name: str
    status: str  # "ready" | "exists_skip" | "exists_overwrite" | "no_key" | "no_source_dir" | "not_found" | "done" | "skipped" | "error"
    error_message: str = ""


def clone_default_config() -> Dict[str, Any]:
    return {
        "work_mode": DEFAULT_WORK_MODE,
        "month_label": DEFAULT_MONTH_LABEL,
        "folder_template": DEFAULT_FOLDER_TEMPLATE,
        "file_fallback_regex": DEFAULT_FILE_FALLBACK_REGEX,
        "ignore_keys": DEFAULT_IGNORE_KEYS,
        "target_regex": DEFAULT_TARGET_REGEX,
        "target_scan": DEFAULT_TARGET_SCAN,
        "aliases": [dict(a) for a in DEFAULT_ALIAS_RULES],
        "rules": [dict(r) for r in DEFAULT_SOURCE_RULES],
    }


def save_logic_config(config: Dict[str, Any], path: str = DEFAULT_LOGIC_CONFIG_PATH) -> str:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    return path


def load_logic_config(path: str = DEFAULT_LOGIC_CONFIG_PATH) -> Dict[str, Any]:
    candidates = [path]
    portable = os.path.join(get_app_dir(), "logic_mapper_rules.json")
    if portable != path:
        candidates.append(portable)

    for candidate in candidates:
        if os.path.exists(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and isinstance(data.get("rules"), list):
                    defaults = clone_default_config()
                    return {
                        "work_mode": str(data.get("work_mode") or defaults["work_mode"]),
                        "month_label": str(data.get("month_label") or defaults["month_label"]),
                        "folder_template": str(data.get("folder_template") or defaults["folder_template"]),
                        "file_fallback_regex": str(
                            data.get("file_fallback_regex")
                            if data.get("file_fallback_regex") is not None
                            else defaults["file_fallback_regex"]
                        ),
                        "ignore_keys": str(
                            data.get("ignore_keys")
                            if data.get("ignore_keys") is not None
                            else defaults["ignore_keys"]
                        ),
                        "target_regex": str(data.get("target_regex") or defaults["target_regex"]),
                        "target_scan": str(data.get("target_scan") or defaults["target_scan"]),
                        "aliases": data["aliases"] if isinstance(data.get("aliases"), list) else defaults["aliases"],
                        "rules": data["rules"],
                    }
            except Exception:
                pass
    return clone_default_config()


def _is_ascii_alnum_only(text: str) -> bool:
    return bool(text) and all(c.isascii() and c.isalnum() for c in text)


def _code_in_filename(code: str, filename: str) -> bool:
    """Check if code appears in filename respecting ASCII alnum boundaries on edges."""
    cleaned = code.strip()
    if not cleaned:
        return False
    escaped = re.escape(cleaned)
    left = r"(?<![A-Za-z0-9])" if (cleaned[0].isascii() and cleaned[0].isalnum()) else ""
    right = r"(?![A-Za-z0-9])" if (cleaned[-1].isascii() and cleaned[-1].isalnum()) else ""
    return re.search(f"{left}{escaped}{right}", filename, flags=re.IGNORECASE) is not None


def extract_key_from_text(text: str, compiled_regex: re.Pattern) -> Optional[str]:
    """Extract capture group 1 (or full match if no capture group) from text."""
    match = compiled_regex.search(text)
    if not match:
        return None
    if match.lastindex and match.lastindex >= 1:
        val = match.group(1)
    else:
        val = match.group(0)
    val = (val or "").strip()
    return val or None


def resolve_pt_for_file(
    filename: str,
    aliases: List[Dict[str, Any]],
    fallback_regex: Optional[re.Pattern],
    ignore_keys: set[str],
) -> Tuple[Optional[str], str]:
    """Resolve (pt_name, month_override) for a raw monthly file using Alias Table then optional regex."""
    active_aliases = [
        a for a in aliases
        if a.get("enabled", True) and str(a.get("match_code", "")).strip() and str(a.get("pt_name", "")).strip()
    ]
    # Longest match_code first so 'PJI-MXZ-26001' always wins before short tokens
    active_aliases.sort(key=lambda a: len(str(a.get("match_code", "")).strip()), reverse=True)

    for alias in active_aliases:
        code = str(alias.get("match_code", "")).strip()
        if _code_in_filename(code, filename):
            return str(alias.get("pt_name", "")).strip(), str(alias.get("month_override", "")).strip()

    if fallback_regex is not None:
        key = extract_key_from_text(filename, fallback_regex)
        if key and key.upper() not in ignore_keys:
            return key, ""

    return None, ""


def format_output_folder_name(
    template: str,
    pt_name: str,
    month_label: str,
    month_override: str = "",
) -> str:
    """Build safe folder name from template e.g. 'PJI-{PT}-{BULAN}物资结算开票资料'."""
    effective_month = month_label.strip()
    override = month_override.strip()
    if override:
        effective_month = (
            override.replace("{BULAN}", effective_month)
            .replace("{MONTH}", effective_month)
            .replace("{月份}", effective_month)
        )

    raw = (
        template.replace("{PT}", pt_name)
        .replace("{KEY}", pt_name)
        .replace("{BULAN}", effective_month)
        .replace("{MONTH}", effective_month)
        .replace("{月份}", effective_month)
    )
    return safe_filename(raw)


def extract_folder_key(
    folder_name: str,
    folder_path: str,
    compiled_regex: re.Pattern,
    scan_mode: str,
) -> Optional[str]:
    """Extract key from existing target folder name, files inside it, or both."""
    mode = (scan_mode or "folder").lower()

    if mode in ("folder", "both"):
        key = extract_key_from_text(folder_name, compiled_regex)
        if key:
            return key
        if mode == "folder":
            return None

    if mode in ("files", "both"):
        try:
            names = sorted(
                (e.name for e in os.scandir(folder_path) if e.is_file()),
                key=lambda s: s.lower(),
            )
        except OSError:
            return None
        for fname in names:
            key = extract_key_from_text(fname, compiled_regex)
            if key:
                return key

    return None


def _file_matches_key(
    filename: str,
    key: str,
    match_mode: str,
    file_pattern: str,
) -> bool:
    """Check whether a source filename matches the extracted key and optional pattern."""
    mode = (match_mode or "token").lower()
    pattern_tpl = (file_pattern or "").strip()

    if mode == "regex":
        raw_expr = pattern_tpl.replace("{KEY}", re.escape(key)) if pattern_tpl else re.escape(key)
        try:
            return re.search(raw_expr, filename, flags=re.IGNORECASE) is not None
        except re.error:
            return False

    if pattern_tpl:
        target = pattern_tpl.replace("{KEY}", key)
        if mode == "contains":
            return target.lower() in filename.lower()
        return _code_in_filename(target, filename)

    if mode == "contains":
        return key.lower() in filename.lower()

    return _code_in_filename(key, filename)


def _collect_source_files(source_dir: str, include_subfolders: bool) -> Tuple[bool, List[Tuple[str, str]]]:
    """Return (dir_accessible, [(filename, full_path), ...])."""
    if not source_dir or not os.path.isdir(source_dir):
        return False, []

    collected: List[Tuple[str, str]] = []
    try:
        if include_subfolders:
            for walk_root, _dirs, files in os.walk(source_dir):
                for fname in sorted(files, key=lambda s: s.lower()):
                    collected.append((fname, os.path.join(walk_root, fname)))
        else:
            for entry in sorted(os.scandir(source_dir), key=lambda e: e.name.lower()):
                if entry.is_file():
                    collected.append((entry.name, entry.path))
    except OSError:
        return False, []
    return True, collected


def _append_source_rule_entries(
    entries: List[LogicMatchEntry],
    folder_name: str,
    folder_path: str,
    key: str,
    active_rules: List[Dict[str, Any]],
    source_cache: Dict[int, Tuple[bool, List[Tuple[str, str]]]],
) -> None:
    """Append matching files from all active source folder rules for one (folder, key)."""
    for idx, rule in enumerate(active_rules):
        rule_name = str(rule.get("name", "")).strip() or f"Rule #{idx + 1}"
        action = str(rule.get("action", "copy")).lower()
        conflict = str(rule.get("conflict", "skip")).lower()
        match_mode = str(rule.get("match_mode", "token")).lower()
        file_pattern = str(rule.get("file_pattern", "")).strip()

        accessible, src_files = source_cache[idx]
        if not accessible:
            entries.append(
                LogicMatchEntry(
                    folder_name=folder_name,
                    folder_path=folder_path,
                    key=key,
                    rule_name=rule_name,
                    action=action,
                    conflict=conflict,
                    source_path="",
                    file_name="",
                    status="no_source_dir",
                )
            )
            continue

        matched_files = [
            (fname, fpath)
            for fname, fpath in src_files
            if _file_matches_key(fname, key, match_mode, file_pattern)
        ]

        if not matched_files:
            entries.append(
                LogicMatchEntry(
                    folder_name=folder_name,
                    folder_path=folder_path,
                    key=key,
                    rule_name=rule_name,
                    action=action,
                    conflict=conflict,
                    source_path="",
                    file_name="",
                    status="not_found",
                )
            )
            continue

        for fname, fpath in matched_files:
            dest_file = os.path.join(folder_path, fname)
            if os.path.exists(dest_file):
                status = "exists_overwrite" if conflict == "overwrite" else "exists_skip"
            else:
                status = "ready"
            entries.append(
                LogicMatchEntry(
                    folder_name=folder_name,
                    folder_path=folder_path,
                    key=key,
                    rule_name=rule_name,
                    action=action,
                    conflict=conflict,
                    source_path=fpath,
                    file_name=fname,
                    status=status,
                )
            )


def build_create_from_files_preview(
    target_root: str,
    month_label: str,
    folder_template: str,
    file_fallback_regex: str,
    ignore_keys_str: str,
    aliases: List[Dict[str, Any]],
    rules: List[Dict[str, Any]],
    monthly_rule_label: str = "Monthly File",
) -> List[LogicMatchEntry]:
    """Mode 1: Scan raw files in target_root, group into created PT folders (MOVE) + inject source rules (COPY/MOVE)."""
    if not target_root or not os.path.isdir(target_root):
        raise ValueError("Target root folder does not exist.")
    if not folder_template.strip():
        raise ValueError("Folder template cannot be empty.")

    compiled_fallback: Optional[re.Pattern] = None
    if file_fallback_regex.strip():
        try:
            compiled_fallback = re.compile(file_fallback_regex.strip(), flags=re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"Invalid fallback regex: {exc}") from exc

    ignore_keys = {
        tok.strip().upper()
        for tok in re.split(r"[,;\s]+", ignore_keys_str or "")
        if tok.strip()
    }

    active_rules = [r for r in rules if r.get("enabled", True)]
    source_cache: Dict[int, Tuple[bool, List[Tuple[str, str]]]] = {}
    for idx, rule in enumerate(active_rules):
        src_dir = str(rule.get("source_dir", "")).strip()
        inc_sub = bool(rule.get("include_subfolders", False))
        source_cache[idx] = _collect_source_files(src_dir, inc_sub)

    raw_files = sorted(
        (
            e
            for e in os.scandir(target_root)
            if e.is_file()
            and e.name.lower() not in IGNORED_SYSTEM_FILES
            and not e.name.startswith("~$")
        ),
        key=lambda e: e.name.lower(),
    )

    # Group recognized files by (folder_name, pt_name)
    grouped: "OrderedDict[Tuple[str, str], List[Tuple[str, str]]]" = OrderedDict()
    unmatched_files: List[Tuple[str, str]] = []

    for fentry in raw_files:
        pt_name, month_override = resolve_pt_for_file(
            fentry.name, aliases, compiled_fallback, ignore_keys
        )
        if not pt_name:
            unmatched_files.append((fentry.name, fentry.path))
            continue

        folder_name = format_output_folder_name(
            folder_template, pt_name, month_label, month_override
        )
        grouped.setdefault((folder_name, pt_name), []).append((fentry.name, fentry.path))

    entries: List[LogicMatchEntry] = []
    for (folder_name, pt_name), file_list in grouped.items():
        folder_path = os.path.join(target_root, folder_name)

        # 1) Monthly files in root -> MOVE into folder_name
        for fname, fpath in file_list:
            dest_file = os.path.join(folder_path, fname)
            status = "exists_overwrite" if os.path.exists(dest_file) else "ready"
            entries.append(
                LogicMatchEntry(
                    folder_name=folder_name,
                    folder_path=folder_path,
                    key=pt_name,
                    rule_name=monthly_rule_label,
                    action="move",
                    conflict="overwrite",
                    source_path=fpath,
                    file_name=fname,
                    status=status,
                )
            )

        # 2) Master files from all active source folder rules (1, 2, 3+)
        _append_source_rule_entries(
            entries, folder_name, folder_path, pt_name, active_rules, source_cache
        )

    for fname, fpath in unmatched_files:
        entries.append(
            LogicMatchEntry(
                folder_name="-",
                folder_path="",
                key="",
                rule_name=monthly_rule_label,
                action="-",
                conflict="skip",
                source_path=fpath,
                file_name=fname,
                status="no_key",
            )
        )

    return entries


def build_logic_preview(
    target_root: str,
    target_regex: str,
    target_scan: str,
    rules: List[Dict[str, Any]],
) -> List[LogicMatchEntry]:
    """Mode 2: Scan existing target subfolders and match files from all enabled source rules."""
    if not target_root or not os.path.isdir(target_root):
        raise ValueError("Target root folder does not exist.")

    try:
        compiled_regex = re.compile(target_regex, flags=re.IGNORECASE)
    except re.error as exc:
        raise ValueError(f"Invalid target regex: {exc}") from exc

    active_rules = [r for r in rules if r.get("enabled", True)]
    if not active_rules:
        raise ValueError("No enabled source folder rules.")

    source_cache: Dict[int, Tuple[bool, List[Tuple[str, str]]]] = {}
    for idx, rule in enumerate(active_rules):
        src_dir = str(rule.get("source_dir", "")).strip()
        inc_sub = bool(rule.get("include_subfolders", False))
        source_cache[idx] = _collect_source_files(src_dir, inc_sub)

    subfolders = sorted(
        (entry for entry in os.scandir(target_root) if entry.is_dir()),
        key=lambda e: e.name.lower(),
    )

    entries: List[LogicMatchEntry] = []
    for folder in subfolders:
        key = extract_folder_key(folder.name, folder.path, compiled_regex, target_scan)
        if not key:
            entries.append(
                LogicMatchEntry(
                    folder_name=folder.name,
                    folder_path=folder.path,
                    key="",
                    rule_name="-",
                    action="-",
                    conflict="skip",
                    source_path="",
                    file_name="",
                    status="no_key",
                )
            )
            continue

        _append_source_rule_entries(
            entries, folder.name, folder.path, key, active_rules, source_cache
        )

    return entries


def execute_logic_mapping(
    entries: List[LogicMatchEntry],
    log: Callable[[str], None],
    progress: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, int]:
    """Execute folder creation and copy/move operations for all previewed LogicMatchEntry rows."""
    processed = 0
    skipped = 0
    missing = 0
    errors = 0
    total = len(entries)

    for idx, entry in enumerate(entries, start=1):
        if entry.status in ("no_key", "no_source_dir", "not_found"):
            missing += 1
            log(f"[MISS] {entry.folder_name} | {entry.file_name or entry.rule_name} | {entry.status}")
            if progress:
                progress(idx, total)
            continue

        if entry.status == "exists_skip":
            entry.status = "skipped"
            skipped += 1
            log(f"[SKIP] {entry.file_name} -> {entry.folder_name} (already exists)")
            if progress:
                progress(idx, total)
            continue

        if not os.path.isfile(entry.source_path):
            entry.status = "not_found"
            missing += 1
            log(f"[NOT FOUND] {entry.source_path}")
            if progress:
                progress(idx, total)
            continue

        try:
            os.makedirs(entry.folder_path, exist_ok=True)
            dest_file = os.path.join(entry.folder_path, entry.file_name)
            if os.path.abspath(entry.source_path).lower() == os.path.abspath(dest_file).lower():
                entry.status = "skipped"
                skipped += 1
                log(f"[SKIP] {entry.file_name} (same source and destination)")
            elif entry.action == "move":
                shutil.move(entry.source_path, dest_file)
                entry.status = "done"
                processed += 1
                log(f"[MOVED] {entry.file_name} -> {entry.folder_name}")
            else:
                shutil.copy2(entry.source_path, dest_file)
                entry.status = "done"
                processed += 1
                log(f"[COPIED] {entry.file_name} -> {entry.folder_name}")
        except Exception as exc:
            entry.status = "error"
            entry.error_message = str(exc)
            errors += 1
            log(f"[ERROR] {entry.file_name} -> {entry.folder_name}: {exc}")

        if progress:
            progress(idx, total)

    return {
        "total": total,
        "processed": processed,
        "skipped": skipped,
        "missing": missing,
        "errors": errors,
    }
