"""Program 4 engine: Universal File & Folder Mover via mapping.xlsx (no Excel COM)."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill


@dataclass
class MoveEntry:
    row: int
    item_name: str
    item_type: str  # "file" | "folder"
    folder_name: str
    source_path: str
    dest_folder: str
    exists: bool
    status: str = "ready"
    error_message: str = ""


def _normalize_item_type(raw_type: Optional[object], source_path: str) -> str:
    """Parse Column C ('file' / 'folder'); auto-detect on disk if blank."""
    text = str(raw_type or "").strip().lower()
    if text in ("folder", "dir", "directory", "文件夹", "目录"):
        return "folder"
    if text in ("file", "文件"):
        return "file"
    if os.path.isdir(source_path):
        return "folder"
    return "file"


def find_mapping_excel(start_folder: str, filename: str = "mapping.xlsx") -> Optional[str]:
    """Search start_folder and its parent directories upward for mapping.xlsx."""
    current = os.path.abspath(start_folder)
    while current:
        candidate = os.path.join(current, filename)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def load_move_entries(root_folder: str, excel_path: str) -> List[MoveEntry]:
    """Read mapping.xlsx from Row 2 (Col A: name, Col B: dest folder, Col C: file/folder)."""
    wb = load_workbook(excel_path, data_only=True)
    try:
        ws = wb.worksheets[0]
        entries: List[MoveEntry] = []
        row_idx = 2
        while True:
            raw_item = ws.cell(row=row_idx, column=1).value
            raw_folder = ws.cell(row=row_idx, column=2).value
            raw_type = ws.cell(row=row_idx, column=3).value

            if raw_item is None or str(raw_item).strip() == "":
                break

            item_name = str(raw_item).strip()
            folder_name = "" if raw_folder is None else str(raw_folder).strip()

            source_path = os.path.join(root_folder, item_name)
            dest_folder = os.path.join(root_folder, folder_name) if folder_name else root_folder
            item_type = _normalize_item_type(raw_type, source_path)

            if item_type == "folder":
                exists = os.path.isdir(source_path)
            else:
                exists = os.path.isfile(source_path)

            entries.append(
                MoveEntry(
                    row=row_idx,
                    item_name=item_name,
                    item_type=item_type,
                    folder_name=folder_name,
                    source_path=source_path,
                    dest_folder=dest_folder,
                    exists=exists,
                    status="ready" if exists else "missing",
                )
            )
            row_idx += 1
        return entries
    finally:
        wb.close()


def _is_subpath(child: str, parent: str) -> bool:
    """Return True if child is identical to or inside parent directory."""
    child_abs = os.path.abspath(child).lower()
    parent_abs = os.path.abspath(parent).lower()
    try:
        return os.path.commonpath([child_abs, parent_abs]) == parent_abs
    except ValueError:
        return False


def execute_file_moves(
    entries: List[MoveEntry],
    log: Callable[[str], None],
    progress: Callable[[int, int], None] | None = None,
) -> Dict[str, int]:
    """Move all existing files and folders into their destination folders."""
    moved = 0
    not_found = 0
    errors = 0
    total = len(entries)

    for idx, entry in enumerate(entries, start=1):
        is_folder = entry.item_type == "folder"
        exists_now = os.path.isdir(entry.source_path) if is_folder else os.path.isfile(entry.source_path)

        if not exists_now:
            entry.status = "missing"
            not_found += 1
            log(f"[NOT FOUND] Row {entry.row} ({entry.item_type}): {entry.source_path}")
            if progress:
                progress(idx, total)
            continue

        try:
            clean_src = entry.source_path.rstrip("\\/")
            base_name = os.path.basename(clean_src)
            target_path = os.path.join(entry.dest_folder, base_name)

            if is_folder and _is_subpath(entry.dest_folder, clean_src):
                raise ValueError("Cannot move a folder into itself.")

            if os.path.abspath(clean_src).lower() == os.path.abspath(target_path).lower():
                entry.status = "moved"
                moved += 1
                log(f"[SKIP SAME] Row {entry.row}: {entry.item_name}")
                if progress:
                    progress(idx, total)
                continue

            os.makedirs(entry.dest_folder, exist_ok=True)
            if os.path.exists(target_path):
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)

            shutil.move(clean_src, target_path)
            entry.status = "moved"
            moved += 1
            tag = "FOLDER" if is_folder else "FILE"
            log(f"[MOVED {tag}] Row {entry.row}: {entry.item_name} -> {entry.folder_name}")
        except Exception as exc:
            entry.status = "error"
            entry.error_message = str(exc)
            errors += 1
            log(f"[ERROR] Row {entry.row}: {entry.item_name} ({exc})")

        if progress:
            progress(idx, total)

    return {
        "total": total,
        "moved": moved,
        "not_found": not_found,
        "errors": errors,
    }


def create_mapping_mockup(output_path: str) -> str:
    """Generate a ready-to-fill mapping.xlsx template with file & folder examples."""
    wb = Workbook()
    ws = wb.active
    ws.title = "mapping"

    headers = ["Nama File / Folder", "Folder Tujuan", "Jenis (file/folder)"]
    ws.append(headers)

    header_fill = PatternFill(start_color="0F6CBD", end_color="0F6CBD", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    for col_idx in range(1, 4):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    sample_rows = [
        ["PO-AMI-N-26036-005.pdf", "PJI-AMI-10月物资结算开票资料", "file"],
        ["PO-AMI-N-26036-005.xlsx", "PJI-AMI-10月物资结算开票资料", "file"],
        ["PJI-AMI-10月物资结算开票资料", "Archive_10月", "folder"],
        ["PJI-TEK-11月中国船物资结算开票资料", "Archive_11月", "folder"],
    ]
    body_font = Font(name="Segoe UI", size=10)
    for row_data in sample_rows:
        ws.append(row_data)
        for col_idx in range(1, 4):
            ws.cell(row=ws.max_row, column=col_idx).font = body_font

    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 36
    ws.column_dimensions["C"].width = 22
    ws.row_dimensions[1].height = 24

    wb.save(output_path)
    wb.close()
    return output_path
