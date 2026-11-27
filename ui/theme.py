"""Modern Windows Fluent / C# WinUI 3 inspired Light & Dark QSS themes."""

from typing import Dict

PALETTES: Dict[str, Dict[str, str]] = {
    "light": {
        "canvas": "#F4F6F9",
        "rail": "#ECEFF4",
        "surface": "#FFFFFF",
        "surface_alt": "#F7F9FC",
        "hover": "#EEF2F7",
        "pressed": "#E2E8F0",
        "border": "#E1E6EF",
        "border_strong": "#CBD3DF",
        "border_bottom": "#D5DCE6",
        "text": "#1A1F29",
        "text_muted": "#525D70",
        "accent": "#0F6CBD",
        "accent_hover": "#115EA3",
        "accent_pressed": "#0C4B85",
        "accent_soft": "#EBF3FC",
        "accent_text": "#FFFFFF",
        "success": "#107C41",
        "warning": "#9A5B00",
        "error": "#C42B1C",
        "table_header": "#F7F9FC",
        "table_row_alt": "#FAFBFD",
        "table_select": "#E5F0FA",
        "table_select_text": "#1A1F29",
        "log_bg": "#F9FAFC",
        "scroll_thumb": "#C5CDD9",
        "scroll_thumb_hover": "#9BA6B8",
        "disabled_bg": "#ECEFF4",
        "disabled_text": "#8C95A4",
    },
    "dark": {
        "canvas": "#16191F",
        "rail": "#1B1F27",
        "surface": "#222731",
        "surface_alt": "#282E3A",
        "hover": "#2E3543",
        "pressed": "#363E4E",
        "border": "#303746",
        "border_strong": "#434C5E",
        "border_bottom": "#12151A",
        "text": "#F2F5F9",
        "text_muted": "#A3AEC0",
        "accent": "#1975C5",
        "accent_hover": "#2486DB",
        "accent_pressed": "#135D9E",
        "accent_soft": "#1C2E42",
        "accent_text": "#FFFFFF",
        "success": "#4ADE80",
        "warning": "#FBBF24",
        "error": "#F87171",
        "table_header": "#262C37",
        "table_row_alt": "#252B36",
        "table_select": "#1E344B",
        "table_select_text": "#F2F5F9",
        "log_bg": "#1A1E26",
        "scroll_thumb": "#434C5E",
        "scroll_thumb_hover": "#5C6880",
        "disabled_bg": "#272C37",
        "disabled_text": "#727C8E",
    },
}


def build_stylesheet(mode: str = "light") -> str:
    p = PALETTES.get(mode, PALETTES["light"])
    return f"""
    QMainWindow, QDialog {{
        background-color: {p['canvas']};
        color: {p['text']};
        font-family: "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
        font-size: 13px;
    }}

    QWidget {{
        color: {p['text']};
        font-family: "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
    }}

    /* Fluent NavigationView Sidebar */
    QFrame#Sidebar {{
        background-color: {p['rail']};
        border-right: 1px solid {p['border']};
    }}

    QFrame#TopBar {{
        background-color: {p['surface']};
        border-bottom: 1px solid {p['border']};
    }}

    /* Fluent Elevated Cards */
    QFrame#Card {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-bottom: 2px solid {p['border_bottom']};
        border-radius: 8px;
    }}

    QFrame#StatCard {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-bottom: 2px solid {p['border_bottom']};
        border-radius: 8px;
    }}

    /* Typography */
    QLabel#BrandTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {p['text']};
    }}

    QLabel#BrandSubtitle {{
        font-size: 11px;
        color: {p['text_muted']};
    }}

    QLabel#NavSection {{
        font-size: 11px;
        font-weight: 600;
        color: {p['text_muted']};
        padding-left: 8px;
        padding-bottom: 2px;
    }}

    QLabel#PageTitle {{
        font-size: 19px;
        font-weight: 700;
        color: {p['text']};
    }}

    QLabel#PageDesc {{
        font-size: 12px;
        color: {p['text_muted']};
    }}

    QLabel#SectionTitle {{
        font-size: 13px;
        font-weight: 600;
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
        border: 1px solid {p['border_strong']};
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 12px;
        font-weight: 600;
        background-color: {p['accent_soft']};
    }}

    QLabel#StatusBanner {{
        background-color: {p['surface_alt']};
        border: 1px solid {p['border']};
        border-radius: 6px;
        padding: 7px 12px;
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
        padding: 14px;
    }}

    /* NavigationView Items */
    QPushButton#NavButton {{
        text-align: left;
        padding: 9px 12px;
        border: 1px solid transparent;
        border-left: 3px solid transparent;
        border-radius: 6px;
        background-color: transparent;
        color: {p['text']};
        font-size: 13px;
        font-weight: 500;
    }}

    QPushButton#NavButton:hover {{
        background-color: {p['hover']};
    }}

    QPushButton#NavButton:pressed {{
        background-color: {p['pressed']};
    }}

    QPushButton#NavButton:checked {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-left: 3px solid {p['accent']};
        color: {p['accent']};
        font-weight: 600;
    }}

    QPushButton#NavButton:focus {{
        border: 2px solid {p['accent']};
    }}

    QFrame#SegmentedBox {{
        background-color: {p['surface_alt']};
        border: 1px solid {p['border']};
        border-radius: 7px;
    }}

    /* Language Segmented Buttons */
    QPushButton#LangButton {{
        padding: 4px 10px;
        border: 1px solid transparent;
        border-radius: 5px;
        background-color: transparent;
        color: {p['text_muted']};
        font-size: 12px;
        font-weight: 600;
        min-width: 34px;
        min-height: 18px;
    }}

    QPushButton#LangButton:hover {{
        background-color: {p['hover']};
        color: {p['text']};
    }}

    QPushButton#LangButton:checked {{
        background-color: {p['accent']};
        border-color: {p['accent']};
        color: {p['accent_text']};
    }}

    QPushButton#LangButton:focus {{
        border: 2px solid {p['accent']};
    }}

    /* Fluent Tinted Secondary Accent Button */
    QPushButton#TintedButton {{
        background-color: {p['accent_soft']};
        color: {p['accent']};
        border: 1px solid {p['border_strong']};
        border-radius: 6px;
        padding: 6px 11px;
        font-weight: 600;
        min-height: 20px;
    }}

    QPushButton#TintedButton:hover {{
        background-color: {p['table_select']};
        border-color: {p['accent']};
    }}

    QPushButton#TintedButton:pressed {{
        background-color: {p['pressed']};
    }}

    QPushButton#TintedButton:focus {{
        border: 2px solid {p['accent']};
    }}

    QPushButton#TintedButton:disabled {{
        background-color: {p['disabled_bg']};
        color: {p['disabled_text']};
        border-color: {p['border']};
    }}

    /* Fluent Standard Buttons */
    QPushButton {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border_strong']};
        border-bottom: 1.5px solid {p['border_bottom']};
        border-radius: 6px;
        padding: 6px 11px;
        font-weight: 500;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: {p['hover']};
        border-color: {p['border_strong']};
    }}

    QPushButton:pressed {{
        background-color: {p['pressed']};
    }}

    QPushButton:focus {{
        border: 2px solid {p['accent']};
    }}

    QPushButton:disabled {{
        background-color: {p['disabled_bg']};
        color: {p['disabled_text']};
        border-color: {p['border']};
    }}

    QPushButton#CollapseButton {{
        padding: 4px 4px;
        min-height: 20px;
        font-weight: 700;
        font-size: 11px;
    }}

    /* Fluent Accent Primary Button */
    QPushButton#PrimaryButton {{
        background-color: {p['accent']};
        color: {p['accent_text']};
        border: 1px solid {p['accent']};
        border-radius: 6px;
        font-weight: 600;
        padding: 7px 18px;
    }}

    QPushButton#PrimaryButton:hover {{
        background-color: {p['accent_hover']};
        border-color: {p['accent_hover']};
    }}

    QPushButton#PrimaryButton:pressed {{
        background-color: {p['accent_pressed']};
        border-color: {p['accent_pressed']};
    }}

    QPushButton#PrimaryButton:focus {{
        border: 2px solid {p['text']};
    }}

    QPushButton#PrimaryButton:disabled {{
        background-color: {p['disabled_bg']};
        color: {p['disabled_text']};
        border-color: {p['border']};
    }}

    /* Fluent Inputs & ComboBox */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border_strong']};
        border-bottom: 1.5px solid {p['border_strong']};
        border-radius: 6px;
        padding: 6px 10px;
        min-height: 20px;
    }}

    QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
        background-color: {p['surface_alt']};
    }}

    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        background-color: {p['surface']};
        border: 1px solid {p['border_strong']};
        border-bottom: 2px solid {p['accent']};
    }}

    QLineEdit[mono="true"] {{
        font-family: "Consolas", "Segoe UI", monospace;
        font-size: 12px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border_strong']};
        border-radius: 6px;
        padding: 4px;
        selection-background-color: {p['table_select']};
        selection-color: {p['table_select_text']};
    }}

    QListWidget {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border']};
        border-radius: 6px;
        padding: 4px;
    }}

    QListWidget::item {{
        padding: 7px 10px;
        border-radius: 5px;
    }}

    QListWidget::item:hover {{
        background-color: {p['hover']};
    }}

    QListWidget::item:selected {{
        background-color: {p['table_select']};
        color: {p['table_select_text']};
        font-weight: 600;
    }}

    QScrollArea {{
        background-color: {p['canvas']};
        border: 1px solid {p['border']};
        border-radius: 8px;
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

    /* Fluent DataGrid Table (Horizontal Dividers Only) */
    QTableWidget {{
        background-color: {p['surface']};
        color: {p['text']};
        gridline-color: transparent;
        border: 1px solid {p['border']};
        border-radius: 8px;
        selection-background-color: {p['table_select']};
        selection-color: {p['table_select_text']};
        alternate-background-color: {p['table_row_alt']};
        outline: 0;
    }}

    QTableWidget::item {{
        padding: 4px 8px;
        border-bottom: 1px solid {p['border']};
    }}

    QTableWidget::item:hover {{
        background-color: {p['hover']};
    }}

    QTableWidget::item:selected {{
        background-color: {p['table_select']};
        color: {p['table_select_text']};
    }}

    QTableWidget:focus {{
        border: 2px solid {p['accent']};
    }}

    QHeaderView::section {{
        background-color: {p['table_header']};
        color: {p['text_muted']};
        border: none;
        border-bottom: 1px solid {p['border']};
        padding: 8px 10px;
        font-weight: 600;
        font-size: 12px;
    }}

    /* Console / Log Box */
    QPlainTextEdit {{
        background-color: {p['log_bg']};
        color: {p['text']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        font-family: "Consolas", "Microsoft YaHei UI", monospace;
        font-size: 12px;
        padding: 8px;
    }}

    QPlainTextEdit:focus {{
        border: 2px solid {p['accent']};
    }}

    /* Fluent Pivot Underline Tabs */
    QTabWidget::pane {{
        border: 1px solid {p['border']};
        border-radius: 8px;
        background-color: {p['surface']};
        margin-top: -1px;
    }}

    QTabBar::tab {{
        background-color: transparent;
        color: {p['text_muted']};
        border: none;
        border-bottom: 2px solid transparent;
        padding: 8px 16px;
        margin-right: 4px;
        font-weight: 600;
    }}

    QTabBar::tab:hover {{
        color: {p['text']};
        background-color: {p['hover']};
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}

    QTabBar::tab:selected {{
        color: {p['accent']};
        border-bottom: 2.5px solid {p['accent']};
    }}

    /* Progress Bar */
    QProgressBar {{
        border: none;
        border-radius: 3px;
        background-color: {p['border']};
        height: 6px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {p['accent']};
        border-radius: 3px;
    }}

    /* Slim Fluent Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 9px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        background: {p['scroll_thumb']};
        min-height: 28px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {p['scroll_thumb_hover']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 9px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal {{
        background: {p['scroll_thumb']};
        min-width: 28px;
        border-radius: 4px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {p['scroll_thumb_hover']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    """
