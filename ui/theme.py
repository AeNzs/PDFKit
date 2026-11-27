"""Warm Paper & Seal Red (Light) and Deep Ink & Seal Red (Dark) QSS themes."""

from typing import Dict

PALETTES: Dict[str, Dict[str, str]] = {
    "light": {
        "canvas": "#F4F1EA",
        "rail": "#EAE5DA",
        "surface": "#FFFFFF",
        "surface_alt": "#F9F7F3",
        "border": "#D5CEC0",
        "border_strong": "#B8AFA0",
        "text": "#1C1E21",
        "text_muted": "#4E5562",
        "accent": "#B42318",
        "accent_hover": "#912018",
        "accent_pressed": "#7A1B14",
        "accent_soft": "#FCECEB",
        "accent_text": "#FFFFFF",
        "success": "#146C43",
        "warning": "#9A5B00",
        "error": "#B42318",
        "table_header": "#EFECE4",
        "table_select": "#F8E2DF",
        "table_select_text": "#1C1E21",
        "watermark": "rgba(28, 30, 33, 24)",
        "log_bg": "#FAF9F6",
        "disabled_bg": "#E8E4DC",
        "disabled_text": "#7A7F88",
    },
    "dark": {
        "canvas": "#141619",
        "rail": "#1A1D22",
        "surface": "#20242B",
        "surface_alt": "#262B34",
        "border": "#333946",
        "border_strong": "#495163",
        "text": "#F2F0EB",
        "text_muted": "#A6AEBC",
        "accent": "#C6362B",
        "accent_hover": "#D84539",
        "accent_pressed": "#A82A20",
        "accent_soft": "#341F21",
        "accent_text": "#FFFFFF",
        "success": "#4ADE80",
        "warning": "#FBBF24",
        "error": "#F87171",
        "table_header": "#262B34",
        "table_select": "#3D2526",
        "table_select_text": "#F2F0EB",
        "watermark": "rgba(242, 240, 235, 22)",
        "log_bg": "#181B20",
        "disabled_bg": "#272C35",
        "disabled_text": "#757D8C",
    },
}


def build_stylesheet(mode: str = "light") -> str:
    p = PALETTES.get(mode, PALETTES["light"])
    return f"""
    QMainWindow, QDialog {{
        background-color: {p['canvas']};
        color: {p['text']};
        font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
        font-size: 13px;
    }}

    QWidget {{
        color: {p['text']};
        font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
    }}

    QFrame#Sidebar {{
        background-color: {p['rail']};
        border-right: 1px solid {p['border']};
    }}

    QFrame#TopBar {{
        background-color: {p['surface']};
        border-bottom: 1px solid {p['border']};
    }}

    QFrame#Card {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-radius: 6px;
    }}

    QFrame#StatCard {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-radius: 6px;
    }}

    QLabel#BrandTitle {{
        font-size: 17px;
        font-weight: 700;
        color: {p['text']};
    }}

    QLabel#BrandSubtitle {{
        font-size: 11px;
        color: {p['text_muted']};
    }}

    QLabel#NavSection {{
        font-size: 11px;
        font-weight: 700;
        color: {p['text_muted']};
        padding-left: 4px;
    }}

    QLabel#PageTitle {{
        font-size: 18px;
        font-weight: 700;
        color: {p['text']};
    }}

    QLabel#PageDesc {{
        font-size: 12px;
        color: {p['text_muted']};
    }}

    QLabel#SectionTitle {{
        font-size: 13px;
        font-weight: 700;
        color: {p['text']};
    }}

    QLabel#FieldLabel {{
        font-size: 12px;
        font-weight: 600;
        color: {p['text_muted']};
    }}

    QLabel#StatValue {{
        font-size: 20px;
        font-weight: 700;
        color: {p['text']};
    }}

    QLabel#StatLabel {{
        font-size: 11px;
        color: {p['text_muted']};
    }}

    QLabel#WatermarkStamp {{
        color: {p['accent']};
        border: 1.5px solid {p['accent']};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: 700;
        background-color: {p['accent_soft']};
    }}

    QLabel#StatusBanner {{
        background-color: {p['surface_alt']};
        border: 1px solid {p['border']};
        border-radius: 4px;
        padding: 6px 10px;
        color: {p['text']};
        font-size: 12px;
    }}

    QLabel#StatusBanner[state="error"] {{
        border-color: {p['error']};
        color: {p['error']};
    }}

    QLabel#StatusBanner[state="done"] {{
        border-color: {p['success']};
        color: {p['success']};
    }}

    QLabel#EmptyHint {{
        color: {p['text_muted']};
        font-size: 12px;
        padding: 12px;
    }}

    /* Sidebar navigation buttons */
    QPushButton#NavButton {{
        text-align: left;
        padding: 10px 12px;
        border: 1px solid transparent;
        border-left: 3px solid transparent;
        border-radius: 4px;
        background-color: transparent;
        color: {p['text']};
        font-size: 13px;
        font-weight: 500;
    }}

    QPushButton#NavButton:hover {{
        background-color: {p['surface_alt']};
    }}

    QPushButton#NavButton:checked {{
        background-color: {p['surface']};
        border-color: {p['border']};
        border-left: 3px solid {p['accent']};
        color: {p['accent']};
        font-weight: 700;
    }}

    QPushButton#NavButton:focus {{
        border: 2px solid {p['accent']};
    }}

    /* Language segmented buttons */
    QPushButton#LangButton {{
        padding: 5px 10px;
        border: 1px solid {p['border']};
        border-radius: 4px;
        background-color: {p['surface_alt']};
        color: {p['text']};
        font-size: 12px;
        font-weight: 600;
        min-width: 38px;
    }}

    QPushButton#LangButton:hover {{
        border-color: {p['border_strong']};
    }}

    QPushButton#LangButton:checked {{
        background-color: {p['accent']};
        border-color: {p['accent']};
        color: {p['accent_text']};
    }}

    QPushButton#LangButton:focus {{
        border: 2px solid {p['accent']};
    }}

    /* Standard & Primary buttons */
    QPushButton {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border_strong']};
        border-radius: 5px;
        padding: 6px 13px;
        font-weight: 500;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: {p['surface_alt']};
        border-color: {p['text_muted']};
    }}

    QPushButton:pressed {{
        background-color: {p['border']};
    }}

    QPushButton:focus {{
        border: 2px solid {p['accent']};
    }}

    QPushButton:disabled {{
        background-color: {p['disabled_bg']};
        color: {p['disabled_text']};
        border-color: {p['border']};
    }}

    QPushButton#PrimaryButton {{
        background-color: {p['accent']};
        color: {p['accent_text']};
        border: 1px solid {p['accent']};
        font-weight: 700;
        padding: 8px 18px;
    }}

    QPushButton#PrimaryButton:hover {{
        background-color: {p['accent_hover']};
        border-color: {p['accent_hover']};
    }}

    QPushButton#PrimaryButton:pressed {{
        background-color: {p['accent_pressed']};
    }}

    QPushButton#PrimaryButton:focus {{
        border: 2px solid {p['text']};
    }}

    QPushButton#PrimaryButton:disabled {{
        background-color: {p['disabled_bg']};
        color: {p['disabled_text']};
        border-color: {p['border']};
    }}

    QLineEdit, QComboBox {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border_strong']};
        border-radius: 4px;
        padding: 6px 8px;
        min-height: 18px;
    }}

    QLineEdit:focus, QComboBox:focus {{
        border: 2px solid {p['accent']};
    }}

    QLineEdit[mono="true"] {{
        font-family: "Consolas", "Segoe UI", monospace;
        font-size: 12px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border_strong']};
        selection-background-color: {p['table_select']};
        selection-color: {p['table_select_text']};
    }}

    QPushButton#CollapseButton {{
        padding: 4px 4px;
        min-height: 20px;
        font-weight: 700;
        font-size: 11px;
    }}

    QSplitter::handle {{
        background-color: transparent;
    }}

    QCheckBox {{
        spacing: 8px;
        color: {p['text']};
        font-size: 13px;
    }}

    QCheckBox:focus {{
        color: {p['accent']};
    }}

    QTableWidget {{
        background-color: {p['surface']};
        color: {p['text']};
        gridline-color: {p['border']};
        border: 1px solid {p['border']};
        border-radius: 5px;
        selection-background-color: {p['table_select']};
        selection-color: {p['table_select_text']};
        alternate-background-color: {p['surface_alt']};
    }}

    QTableWidget:focus {{
        border: 2px solid {p['accent']};
    }}

    QHeaderView::section {{
        background-color: {p['table_header']};
        color: {p['text']};
        border: none;
        border-right: 1px solid {p['border']};
        border-bottom: 1px solid {p['border']};
        padding: 6px 8px;
        font-weight: 600;
        font-size: 12px;
    }}

    QPlainTextEdit {{
        background-color: {p['log_bg']};
        color: {p['text']};
        border: 1px solid {p['border']};
        border-radius: 5px;
        font-family: "Consolas", "Microsoft YaHei UI", monospace;
        font-size: 12px;
        padding: 6px;
    }}

    QPlainTextEdit:focus {{
        border: 2px solid {p['accent']};
    }}

    QTabWidget::pane {{
        border: 1px solid {p['border']};
        border-radius: 5px;
        background-color: {p['surface']};
    }}

    QTabBar::tab {{
        background-color: {p['rail']};
        color: {p['text_muted']};
        border: 1px solid {p['border']};
        border-bottom: none;
        padding: 6px 14px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-weight: 600;
    }}

    QTabBar::tab:selected {{
        background-color: {p['surface']};
        color: {p['accent']};
    }}

    QProgressBar {{
        border: 1px solid {p['border']};
        border-radius: 4px;
        background-color: {p['surface_alt']};
        height: 8px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {p['accent']};
        border-radius: 3px;
    }}
    """
