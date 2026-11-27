"""Program 1 engine: PDF Split by Excel keyword + Automatic Image Signature."""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Callable, Dict, List

import pymupdf
from openpyxl import load_workbook


def get_app_dir() -> str:
    """Return directory next to the frozen executable or project root."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path: str) -> str:
    """Resolve bundled asset path for both PyInstaller and source runs."""
    base = getattr(sys, "_MEIPASS", get_app_dir())
    for candidate in (
        os.path.join(base, relative_path),
        os.path.join(base, os.path.basename(relative_path)),
        os.path.join(get_app_dir(), relative_path),
    ):
        if os.path.exists(candidate):
            return candidate
    return os.path.join(get_app_dir(), relative_path)


def get_config_path() -> str:
    """Return writable signature_rules.json path (per-user AppData for installed apps)."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        cfg_dir = os.path.join(appdata, "PDF整理工具")
        os.makedirs(cfg_dir, exist_ok=True)
        return os.path.join(cfg_dir, "signature_rules.json")
    return os.path.join(get_app_dir(), "signature_rules.json")


DEFAULT_CONFIG_PATH = get_config_path()

DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "enabled": True,
        "base": "text",
        "anchor": "Prepared By",
        "image": "邓双涛.png",
        "offset_x": -5.0,
        "offset_y": 18.0,
        "width": 60.0,
        "height": 43.0,
        "page": "all",
    },
    {
        "enabled": True,
        "base": "text",
        "anchor": "Receiving olerk,",
        "image": "王新平.png",
        "offset_x": -5.0,
        "offset_y": 18.0,
        "width": 60.0,
        "height": 43.0,
        "page": "all",
    },
    {
        "enabled": True,
        "base": "text",
        "anchor": "Check By,",
        "image": "张园园.png",
        "offset_x": -5.0,
        "offset_y": 18.0,
        "width": 60.0,
        "height": 43.0,
        "page": "all",
    },
]


def safe_filename(filename: Any) -> str:
    value = str(filename).strip()
    value = re.sub(r'[\\/:*?"<>|]', "_", value)
    value = value.rstrip(" .")
    return value or "output"


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    value = str(text).lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def clone_default_rules() -> List[Dict[str, Any]]:
    return [dict(rule) for rule in DEFAULT_RULES]


def save_rules(rules: List[Dict[str, Any]], path: str = DEFAULT_CONFIG_PATH) -> str:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=4, ensure_ascii=False)
    return path


def load_rules(path: str = DEFAULT_CONFIG_PATH) -> List[Dict[str, Any]]:
    candidates = [path]
    portable_seed = os.path.join(get_app_dir(), "signature_rules.json")
    if portable_seed != path:
        candidates.append(portable_seed)
    for candidate in candidates:
        if os.path.exists(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                if isinstance(rules, list):
                    return rules
            except Exception:
                pass
    return clone_default_rules()


def load_split_excel(excel_path: str) -> List[Dict[str, Any]]:
    """Read Column A (keyword) and Column B (output filename) from active sheet."""
    wb = load_workbook(excel_path, data_only=True)
    try:
        ws = wb.active
        data: List[Dict[str, Any]] = []
        for row in ws.iter_rows(min_row=1, values_only=True):
            keyword = row[0] if len(row) > 0 else None
            filename = row[1] if len(row) > 1 else None
            if keyword is None or filename is None:
                continue
            keyword_str = str(keyword).strip()
            filename_str = safe_filename(filename)
            if keyword_str:
                data.append(
                    {
                        "keyword": keyword_str,
                        "filename": filename_str,
                        "pages": [],
                    }
                )
        return data
    finally:
        wb.close()


def split_pdf(
    pdf_path: str,
    excel_path: str,
    split_dir: str,
    log: Callable[[str], None],
    progress: Callable[[int, int], None] | None = None,
) -> List[str]:
    items = load_split_excel(excel_path)
    if not items:
        raise ValueError("No valid data found in Excel columns A and B.")

    os.makedirs(split_dir, exist_ok=True)
    log(f"[INFO] Excel keywords loaded: {len(items)}")

    doc = pymupdf.open(pdf_path)
    try:
        total_pages = len(doc)
        for page_number in range(total_pages):
            page = doc[page_number]
            page_text = normalize_text(page.get_text("text"))
            for item in items:
                keyword = normalize_text(item["keyword"])
                if keyword in page_text:
                    item["pages"].append(page_number)
            log(f"[SCAN] Page {page_number + 1}/{total_pages}")
            if progress:
                progress(page_number + 1, total_pages)

        result: List[str] = []
        for item in items:
            if not item["pages"]:
                log(f"[NOT FOUND] {item['keyword']}")
                continue

            filename = item["filename"]
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"

            output_path = os.path.join(split_dir, filename)
            if os.path.exists(output_path):
                base, ext = os.path.splitext(output_path)
                n = 2
                while os.path.exists(f"{base}_{n}{ext}"):
                    n += 1
                output_path = f"{base}_{n}{ext}"

            new_doc = pymupdf.open()
            try:
                for page_number in item["pages"]:
                    new_doc.insert_pdf(doc, from_page=page_number, to_page=page_number)
                new_doc.save(output_path)
            finally:
                new_doc.close()

            result.append(output_path)
            log(f"[SPLIT] {os.path.basename(output_path)} ({len(item['pages'])} page(s))")

        return result
    finally:
        doc.close()


def page_matches(rule: Dict[str, Any], page_number: int, page_count: int) -> bool:
    value = str(rule.get("page", "all")).strip().lower()
    if value in ("", "all", "semua"):
        return True
    if value == "first":
        return page_number == 0
    if value == "last":
        return page_number == page_count - 1
    if value.isdigit():
        return page_number == int(value) - 1
    return True


def resolve_image_path(signature_dir: str, image_name: str) -> str:
    cleaned = image_name.strip()
    if os.path.isabs(cleaned):
        return cleaned
    return os.path.join(signature_dir, cleaned)


def insert_signature_by_text(page: pymupdf.Page, rule: Dict[str, Any], image_path: str) -> bool:
    anchor = str(rule.get("anchor", ""))
    if not anchor:
        return False
    rects = page.search_for(anchor)
    if not rects:
        return False

    r = rects[0]
    x = float(rule.get("offset_x", 0))
    y = float(rule.get("offset_y", 0))
    width = float(rule.get("width", 60))
    height = float(rule.get("height", 43))

    sign_rect = pymupdf.Rect(r.x0 + x, r.y0 + y, r.x0 + x + width, r.y0 + y + height)
    page.insert_image(sign_rect, filename=image_path, keep_proportion=True, overlay=True)
    return True


def insert_signature_by_coordinate(page: pymupdf.Page, rule: Dict[str, Any], image_path: str) -> bool:
    x = float(rule.get("offset_x", 0))
    y = float(rule.get("offset_y", 0))
    width = float(rule.get("width", 60))
    height = float(rule.get("height", 43))

    sign_rect = pymupdf.Rect(x, y, x + width, y + height)
    page.insert_image(sign_rect, filename=image_path, keep_proportion=True, overlay=True)
    return True


def sign_pdf(
    pdf_path: str,
    signed_path: str,
    rules: List[Dict[str, Any]],
    signature_dir: str,
    log: Callable[[str], None],
) -> None:
    doc = pymupdf.open(pdf_path)
    try:
        counters: List[Dict[str, Any]] = []
        for rule_index, rule in enumerate(rules):
            if not rule.get("enabled", True):
                continue
            image_name = str(rule.get("image", "")).strip()
            if not image_name:
                log(f"[SKIP] Rule {rule_index + 1}: empty signature image")
                continue
            image_path = resolve_image_path(signature_dir, image_name)
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Signature image not found:\n{image_path}")
            counters.append(
                {
                    "index": rule_index + 1,
                    "rule": rule,
                    "image_path": image_path,
                    "count": 0,
                }
            )

        page_count = len(doc)
        for page_number, page in enumerate(doc):
            for item in counters:
                rule = item["rule"]
                if not page_matches(rule, page_number, page_count):
                    continue
                base = str(rule.get("base", "text")).lower()
                if base == "coordinate":
                    inserted = insert_signature_by_coordinate(page, rule, item["image_path"])
                else:
                    inserted = insert_signature_by_text(page, rule, item["image_path"])
                if inserted:
                    item["count"] += 1

        doc.save(signed_path, garbage=4, deflate=True)
    finally:
        doc.close()

    for item in counters:
        rule = item["rule"]
        if str(rule.get("base", "text")).lower() == "coordinate":
            target = f"coordinate ({rule.get('offset_x')}, {rule.get('offset_y')})"
        else:
            target = str(rule.get("anchor", ""))
        log(f"[SIGN] {os.path.basename(signed_path)} | Rule {item['index']} | {target} | {item['count']} page(s)")


def run_split_and_sign(
    pdf_path: str,
    excel_path: str,
    output_dir: str,
    signature_dir: str,
    rules: List[Dict[str, Any]],
    log: Callable[[str], None],
    progress: Callable[[int, int], None] | None = None,
) -> Dict[str, Any]:
    split_dir = os.path.join(output_dir, "Split")
    signed_dir = os.path.join(output_dir, "Signed")

    split_files = split_pdf(pdf_path, excel_path, split_dir, log, progress=progress)
    if not split_files:
        raise ValueError("No PDF pages matched any keyword in the Excel file.")

    os.makedirs(signed_dir, exist_ok=True)
    total_files = len(split_files)
    for idx, split_file in enumerate(split_files, start=1):
        filename = os.path.basename(split_file)
        signed_path = os.path.join(signed_dir, filename)
        sign_pdf(split_file, signed_path, rules, signature_dir, log)
        if progress:
            progress(idx, total_files)

    return {
        "split_dir": split_dir,
        "signed_dir": signed_dir,
        "files": split_files,
        "count": len(split_files),
    }
