"""Programs 2, 3, 5 engine: Folder and PDF/Excel file list exporters."""

from __future__ import annotations

import os
from typing import Dict, List

TARGET_EXTENSIONS = {".pdf", ".xls", ".xlsx"}


def _is_target_doc(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in TARGET_EXTENSIONS


def generate_folder_list(root_dir: str) -> str:
    """Program 2: list immediate subdirectories into folderlist.txt."""
    folders = sorted(
        (
            entry.name
            for entry in os.scandir(root_dir)
            if entry.is_dir()
        ),
        key=lambda s: s.lower(),
    )
    return "\n".join(folders) + ("\n" if folders else "")


def generate_file_list(root_dir: str) -> str:
    """Program 5: list immediate .xlsx, .xls, .pdf files into filelist.txt."""
    files = sorted(
        (
            entry.name
            for entry in os.scandir(root_dir)
            if entry.is_file() and _is_target_doc(entry.name)
        ),
        key=lambda s: s.lower(),
    )
    return "\n".join(files) + ("\n" if files else "")


def generate_folder_file_list(root_dir: str) -> str:
    """Program 3: list subdirectories and their .pdf/.xls/.xlsx files into folder_file_list.txt."""
    folders = sorted(
        (entry for entry in os.scandir(root_dir) if entry.is_dir()),
        key=lambda e: e.name.lower(),
    )
    lines: List[str] = []
    for folder in folders:
        lines.append(folder.name)
        try:
            docs = sorted(
                (
                    child.name
                    for child in os.scandir(folder.path)
                    if child.is_file() and _is_target_doc(child.name)
                ),
                key=lambda s: s.lower(),
            )
        except PermissionError:
            docs = []

        for doc_name in docs:
            lines.append(f"- {doc_name}")
        lines.append("")

    return "\n".join(lines) + ("\n" if lines else "")


def preview_exports(
    root_dir: str,
    include_folders: bool,
    include_files: bool,
    include_folder_files: bool,
) -> Dict[str, str]:
    """Return mapping of output filename -> generated text content."""
    outputs: Dict[str, str] = {}
    if include_folders:
        outputs["folderlist.txt"] = generate_folder_list(root_dir)
    if include_files:
        outputs["filelist.txt"] = generate_file_list(root_dir)
    if include_folder_files:
        outputs["folder_file_list.txt"] = generate_folder_file_list(root_dir)
    return outputs


def write_exports(
    root_dir: str,
    include_folders: bool,
    include_files: bool,
    include_folder_files: bool,
) -> List[str]:
    """Write selected .txt list files in UTF-8 into root_dir and return created file paths."""
    contents = preview_exports(
        root_dir,
        include_folders=include_folders,
        include_files=include_files,
        include_folder_files=include_folder_files,
    )
    written: List[str] = []
    for filename, text in contents.items():
        output_path = os.path.join(root_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        written.append(output_path)
    return written
