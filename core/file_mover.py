"""Program 4 engine: Universal File Moving via mapping.xlsx (no Excel COM required)."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from openpyxl import load_workbook


@dataclass
class MoveEntry:
    row: int
    filename: str
    folder_name: str
    source_path: str
    dest_folder: str
    exists: bool
    status: str = "ready"
    error_message: str = ""


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
    """Read mapping.xlsx starting from Row 2 (Col A = file name, Col B = folder name)."""
    wb = load_workbook(excel_path, data_only=True)
    try:
        ws = wb.worksheets[0]
        entries: List[MoveEntry] = []
        row_idx = 2
        while True:
            raw_file = ws.cell(row=row_idx, column=1).value
            raw_folder = ws.cell(row=row_idx, column=2).value

            if raw_file is None or str(raw_file).strip() == "":
                break

            file_name = str(raw_file).strip()
            folder_name = "" if raw_folder is None else str(raw_folder).strip()

            source_path = os.path.join(root_folder, file_name)
            dest_folder = os.path.join(root_folder, folder_name) if folder_name else root_folder
            exists = os.path.isfile(source_path)

            entries.append(
                MoveEntry(
                    row=row_idx,
                    filename=file_name,
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


def execute_file_moves(
    entries: List[MoveEntry],
    log: Callable[[str], None],
    progress: Callable[[int, int], None] | None = None,
) -> Dict[str, int]:
    """Move all existing entries into their destination folders (overwriting duplicates)."""
    moved = 0
    not_found = 0
    errors = 0
    total = len(entries)

    for idx, entry in enumerate(entries, start=1):
        if not os.path.isfile(entry.source_path):
            entry.status = "missing"
            not_found += 1
            log(f"[NOT FOUND] Row {entry.row}: {entry.source_path}")
            if progress:
                progress(idx, total)
            continue

        try:
            os.makedirs(entry.dest_folder, exist_ok=True)
            target_file = os.path.join(entry.dest_folder, os.path.basename(entry.source_path))
            shutil.move(entry.source_path, target_file)
            entry.status = "moved"
            moved += 1
            log(f"[MOVED] Row {entry.row}: {entry.filename} -> {entry.folder_name}")
        except Exception as exc:
            entry.status = "error"
            entry.error_message = str(exc)
            errors += 1
            log(f"[ERROR] Row {entry.row}: {entry.filename} ({exc})")

        if progress:
            progress(idx, total)

    return {
        "total": total,
        "moved": moved,
        "not_found": not_found,
        "errors": errors,
    }
