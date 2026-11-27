"""Interactive PDF Signature Placement Preview and Coordinate Picker."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import pymupdf
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.i18n import I18n
from core.pdf_sign import page_matches, resolve_image_path


HANDLE_SIZE = 10.0


class PdfPreviewCanvas(QWidget):
    """Renders one PDF page with draggable/resizable signature rule overlays."""

    cursor_moved = Signal(float, float)
    rule_selected = Signal(int)
    rule_geometry_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._page_pixmap: Optional[QPixmap] = None
        self._page_width_pt: float = 595.0
        self._page_height_pt: float = 842.0
        self._zoom: float = 1.25

        self._rules: List[Dict[str, Any]] = []
        self._signature_dir: str = ""
        self._page_index: int = 0
        self._page_count: int = 1
        self._anchor_rects: Dict[int, Optional[pymupdf.Rect]] = {}
        self._image_cache: Dict[str, QPixmap] = {}
        self._selected_index: int = -1

        self._drag_mode: Optional[str] = None  # "move" or "resize"
        self._drag_rule_idx: int = -1
        self._drag_start_pt: QPointF = QPointF()
        self._drag_orig_values: Tuple[float, float, float, float] = (0.0, 0.0, 60.0, 43.0)

    def set_page_data(
        self,
        page: pymupdf.Page,
        page_index: int,
        page_count: int,
        zoom: float,
        rules: List[Dict[str, Any]],
        signature_dir: str,
    ) -> None:
        self._zoom = zoom
        self._page_index = page_index
        self._page_count = page_count
        self._rules = rules
        self._signature_dir = signature_dir

        rect = page.rect
        self._page_width_pt = float(rect.width)
        self._page_height_pt = float(rect.height)

        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
        self._page_pixmap = QPixmap.fromImage(img)

        self._anchor_rects.clear()
        for idx, rule in enumerate(rules):
            if str(rule.get("base", "text")).lower() == "text":
                anchor = str(rule.get("anchor", "")).strip()
                rects = page.search_for(anchor) if anchor else []
                self._anchor_rects[idx] = rects[0] if rects else None
            else:
                self._anchor_rects[idx] = None

        self.setFixedSize(self._page_pixmap.size())
        self.update()

    def set_selected_rule(self, index: int) -> None:
        self._selected_index = index
        self.update()

    def anchor_rect_for(self, index: int) -> Optional[pymupdf.Rect]:
        return self._anchor_rects.get(index)

    def rule_pdf_rect(self, index: int) -> Optional[QRectF]:
        if not (0 <= index < len(self._rules)):
            return None
        rule = self._rules[index]
        if not rule.get("enabled", True):
            return None
        if not page_matches(rule, self._page_index, self._page_count):
            return None

        base = str(rule.get("base", "text")).lower()
        x = float(rule.get("offset_x", 0))
        y = float(rule.get("offset_y", 0))
        w = max(8.0, float(rule.get("width", 60)))
        h = max(8.0, float(rule.get("height", 43)))

        if base == "coordinate":
            return QRectF(x, y, w, h)

        anchor_r = self._anchor_rects.get(index)
        if anchor_r is None:
            return None
        return QRectF(anchor_r.x0 + x, anchor_r.y0 + y, w, h)

    def _pdf_to_widget_rect(self, r: QRectF) -> QRectF:
        z = self._zoom
        return QRectF(r.x() * z, r.y() * z, r.width() * z, r.height() * z)

    def _widget_to_pdf_point(self, pos: QPointF) -> QPointF:
        z = self._zoom if self._zoom > 0 else 1.0
        return QPointF(pos.x() / z, pos.y() / z)

    def _get_signature_pixmap(self, image_name: str) -> Optional[QPixmap]:
        if not image_name:
            return None
        path = resolve_image_path(self._signature_dir, image_name)
        if not os.path.isfile(path):
            return None
        cached = self._image_cache.get(path)
        if cached is not None:
            return cached
        pm = QPixmap(path)
        if pm.isNull():
            return None
        self._image_cache[path] = pm
        return pm

    def _resize_handle_rect(self, wrect: QRectF) -> QRectF:
        return QRectF(
            wrect.right() - HANDLE_SIZE,
            wrect.bottom() - HANDLE_SIZE,
            HANDLE_SIZE,
            HANDLE_SIZE,
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self._page_pixmap is not None:
            painter.drawPixmap(0, 0, self._page_pixmap)

        label_font = QFont("Segoe UI", 8)
        label_font.setBold(True)
        painter.setFont(label_font)

        for idx, rule in enumerate(self._rules):
            is_selected = idx == self._selected_index

            # Draw anchor highlight for text-based rules
            anchor_r = self._anchor_rects.get(idx)
            if anchor_r is not None and rule.get("enabled", True):
                a_wrect = self._pdf_to_widget_rect(
                    QRectF(anchor_r.x0, anchor_r.y0, anchor_r.width, anchor_r.height)
                )
                pen = QPen(QColor("#1D4ED8") if is_selected else QColor(29, 78, 216, 130), 1.5, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QColor(29, 78, 216, 26))
                painter.drawRect(a_wrect)

            pdf_rect = self.rule_pdf_rect(idx)
            if pdf_rect is None:
                continue

            wrect = self._pdf_to_widget_rect(pdf_rect)

            # Draw actual signature image keeping proportion (matching PyMuPDF insert_image)
            pm = self._get_signature_pixmap(str(rule.get("image", "")))
            if pm is not None:
                scaled = pm.scaled(
                    int(max(1, wrect.width())),
                    int(max(1, wrect.height())),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                dx = wrect.x() + (wrect.width() - scaled.width()) / 2.0
                dy = wrect.y() + (wrect.height() - scaled.height()) / 2.0
                painter.drawPixmap(QPointF(dx, dy), scaled)
            else:
                painter.fillRect(wrect, QColor(180, 35, 24, 30))

            # Draw border and rule tag
            border_color = QColor("#0F6CBD") if is_selected else QColor("#0F766E")
            painter.setPen(QPen(border_color, 2.0 if is_selected else 1.4))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(wrect)

            tag = f"#{idx + 1} {os.path.basename(str(rule.get('image', '') or 'TTD'))}"
            tag_w = max(wrect.width(), painter.fontMetrics().horizontalAdvance(tag) + 10)
            tag_y = wrect.bottom() + 2.0
            if tag_y + 16.0 > self.height():
                tag_y = max(0.0, wrect.top() - 17.0)
            tag_rect = QRectF(wrect.x(), tag_y, tag_w, 16.0)
            painter.fillRect(tag_rect, border_color)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(tag_rect.adjusted(4, 0, -4, 0), Qt.AlignVCenter | Qt.AlignLeft, tag)

            if is_selected:
                handle = self._resize_handle_rect(wrect)
                painter.fillRect(handle, QColor("#0F6CBD"))
                painter.setPen(QPen(QColor("#FFFFFF"), 1.0))
                painter.drawRect(handle)

        painter.end()

    def _hit_test(self, pos: QPointF) -> Tuple[Optional[str], int]:
        # Check selected rule first so overlapping drag/resize feels natural
        order = list(range(len(self._rules) - 1, -1, -1))
        if 0 <= self._selected_index < len(self._rules):
            order.remove(self._selected_index)
            order.insert(0, self._selected_index)

        for idx in order:
            pdf_rect = self.rule_pdf_rect(idx)
            if pdf_rect is None:
                continue
            wrect = self._pdf_to_widget_rect(pdf_rect)
            if idx == self._selected_index and self._resize_handle_rect(wrect).adjusted(-3, -3, 3, 3).contains(pos):
                return "resize", idx
            if wrect.contains(pos):
                return "move", idx
        return None, -1

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.LeftButton:
            return
        pos = event.position()
        mode, idx = self._hit_test(pos)
        if idx != -1:
            self._selected_index = idx
            self.rule_selected.emit(idx)
            self._drag_mode = mode
            self._drag_rule_idx = idx
            self._drag_start_pt = self._widget_to_pdf_point(pos)
            rule = self._rules[idx]
            self._drag_orig_values = (
                float(rule.get("offset_x", 0)),
                float(rule.get("offset_y", 0)),
                float(rule.get("width", 60)),
                float(rule.get("height", 43)),
            )
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position()
        pt = self._widget_to_pdf_point(pos)
        self.cursor_moved.emit(pt.x(), pt.y())

        if self._drag_mode and 0 <= self._drag_rule_idx < len(self._rules):
            rule = self._rules[self._drag_rule_idx]
            ox, oy, ow, oh = self._drag_orig_values
            dx = pt.x() - self._drag_start_pt.x()
            dy = pt.y() - self._drag_start_pt.y()

            if self._drag_mode == "move":
                rule["offset_x"] = round(ox + dx, 1)
                rule["offset_y"] = round(oy + dy, 1)
            elif self._drag_mode == "resize":
                rule["width"] = round(max(10.0, ow + dx), 1)
                rule["height"] = round(max(10.0, oh + dy), 1)

            self.rule_geometry_changed.emit(self._drag_rule_idx)
            self.update()
            return

        mode, _idx = self._hit_test(pos)
        if mode == "resize":
            self.setCursor(Qt.SizeFDiagCursor)
        elif mode == "move":
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._drag_mode:
            self._drag_mode = None
            self._drag_rule_idx = -1
            self.setCursor(Qt.CrossCursor)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Move currently selected rule's top-left corner to double-clicked PDF coordinate."""
        if event.button() != Qt.LeftButton:
            return
        if not (0 <= self._selected_index < len(self._rules)):
            return
        rule = self._rules[self._selected_index]
        pt = self._widget_to_pdf_point(event.position())
        base = str(rule.get("base", "text")).lower()

        if base == "coordinate":
            rule["offset_x"] = round(pt.x(), 1)
            rule["offset_y"] = round(pt.y(), 1)
        else:
            anchor_r = self._anchor_rects.get(self._selected_index)
            if anchor_r is None:
                return
            rule["offset_x"] = round(pt.x() - anchor_r.x0, 1)
            rule["offset_y"] = round(pt.y() - anchor_r.y0, 1)

        self.rule_geometry_changed.emit(self._selected_index)
        self.update()


class SignaturePreviewDialog(QDialog):
    """Interactive PDF preview dialog for visually tracking and editing signature coordinates."""

    def __init__(
        self,
        i18n: I18n,
        pdf_path: str,
        rules: List[Dict[str, Any]],
        signature_dir: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self._pdf_path = pdf_path
        self._signature_dir = signature_dir
        # Work on a deep copy so Cancel leaves original rules untouched
        self.edited_rules: List[Dict[str, Any]] = [dict(r) for r in rules]
        self._doc = pymupdf.open(pdf_path)
        self._page_count = len(self._doc)
        self._current_page = 0
        self._zoom = 1.25
        self._syncing_controls = False

        self.setModal(True)
        self.resize(1120, 760)
        self.setMinimumSize(860, 600)
        self.setWindowTitle(self.i18n.t("preview_dlg_title"))

        self._build_ui()
        self._render_current_page()
        if self.edited_rules:
            self.rule_list.setCurrentRow(0)

    def closeEvent(self, event) -> None:
        try:
            self._doc.close()
        except Exception:
            pass
        super().closeEvent(event)

    def _build_ui(self) -> None:
        t = self.i18n.t
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 14)
        root.setSpacing(10)

        # Top toolbar: page navigation + zoom + live PDF cursor coordinates
        toolbar = QFrame()
        toolbar.setObjectName("Card")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 8, 12, 8)
        tb.setSpacing(8)

        self.prev_btn = QPushButton("<")
        self.prev_btn.setObjectName("CollapseButton")
        self.prev_btn.setFixedWidth(34)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(lambda: self._go_page(self._current_page - 1))

        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, max(1, self._page_count))
        self.page_spin.setValue(1)
        self.page_spin.valueChanged.connect(lambda v: self._go_page(v - 1))

        page_total_lbl = QLabel(f"/ {self._page_count}")
        page_total_lbl.setObjectName("FieldLabel")

        self.next_btn = QPushButton(">")
        self.next_btn.setObjectName("CollapseButton")
        self.next_btn.setFixedWidth(34)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(lambda: self._go_page(self._current_page + 1))

        zoom_lbl = QLabel(t("preview_zoom_label"))
        zoom_lbl.setObjectName("FieldLabel")
        self.zoom_combo = QComboBox()
        for pct in (75, 100, 125, 150, 200):
            self.zoom_combo.addItem(f"{pct}%", pct / 100.0)
        self.zoom_combo.setCurrentIndex(2)  # 125%
        self.zoom_combo.currentIndexChanged.connect(self._on_zoom_changed)

        self.cursor_lbl = QLabel(t("preview_cursor_fmt", x=0.0, y=0.0))
        self.cursor_lbl.setObjectName("SectionTitle")

        tb.addWidget(QLabel(t("preview_page_label")))
        tb.addWidget(self.prev_btn)
        tb.addWidget(self.page_spin)
        tb.addWidget(page_total_lbl)
        tb.addWidget(self.next_btn)
        tb.addSpacing(14)
        tb.addWidget(zoom_lbl)
        tb.addWidget(self.zoom_combo)
        tb.addStretch(1)
        tb.addWidget(self.cursor_lbl)
        root.addWidget(toolbar)

        hint_lbl = QLabel(t("preview_hint"))
        hint_lbl.setObjectName("PageDesc")
        hint_lbl.setWordWrap(True)
        root.addWidget(hint_lbl)

        # Center area: scrollable PDF canvas on left + rule coordinate inspector on right
        body = QHBoxLayout()
        body.setSpacing(12)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setAlignment(Qt.AlignCenter)

        self.canvas = PdfPreviewCanvas()
        self.canvas.cursor_moved.connect(self._on_cursor_moved)
        self.canvas.rule_selected.connect(self._on_canvas_rule_selected)
        self.canvas.rule_geometry_changed.connect(self._on_canvas_geometry_changed)
        self.scroll.setWidget(self.canvas)
        body.addWidget(self.scroll, 3)

        # Right inspector card
        inspector = QFrame()
        inspector.setObjectName("Card")
        inspector.setFixedWidth(310)
        insp = QVBoxLayout(inspector)
        insp.setContentsMargins(14, 14, 14, 14)
        insp.setSpacing(10)

        list_title = QLabel(t("preview_rules_list"))
        list_title.setObjectName("SectionTitle")
        insp.addWidget(list_title)

        self.rule_list = QListWidget()
        self.rule_list.setMaximumHeight(210)
        self.rule_list.currentRowChanged.connect(self._on_list_row_changed)
        insp.addWidget(self.rule_list)

        coord_title = QLabel(t("preview_selected_rule"))
        coord_title.setObjectName("SectionTitle")
        insp.addWidget(coord_title)

        self.rule_status_lbl = QLabel("")
        self.rule_status_lbl.setObjectName("StatusBanner")
        self.rule_status_lbl.setWordWrap(True)
        insp.addWidget(self.rule_status_lbl)

        form = QFormLayout()
        form.setSpacing(8)

        self.base_combo = QComboBox()
        self.base_combo.addItem(t("val_text"), "text")
        self.base_combo.addItem(t("val_coordinate"), "coordinate")
        self.base_combo.currentIndexChanged.connect(self._on_spin_edited)

        self.spin_x = self._make_spin(-2000.0, 4000.0)
        self.spin_y = self._make_spin(-2000.0, 4000.0)
        self.spin_w = self._make_spin(10.0, 2000.0)
        self.spin_h = self._make_spin(10.0, 2000.0)

        form.addRow(t("rule_base_label"), self.base_combo)
        form.addRow(t("rule_offset_x_label"), self.spin_x)
        form.addRow(t("rule_offset_y_label"), self.spin_y)
        form.addRow(t("rule_width_label"), self.spin_w)
        form.addRow(t("rule_height_label"), self.spin_h)
        insp.addLayout(form)
        insp.addStretch(1)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton(t("btn_cancel"))
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        apply_btn = QPushButton(t("preview_btn_apply"))
        apply_btn.setObjectName("PrimaryButton")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(apply_btn, 1)
        insp.addLayout(btn_row)

        body.addWidget(inspector)
        root.addLayout(body, 1)

    def _make_spin(self, low: float, high: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(low, high)
        spin.setDecimals(1)
        spin.setSingleStep(1.0)
        spin.valueChanged.connect(self._on_spin_edited)
        return spin

    def _go_page(self, index: int) -> None:
        clamped = max(0, min(self._page_count - 1, index))
        if clamped == self._current_page:
            return
        self._current_page = clamped
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(clamped + 1)
        self.page_spin.blockSignals(False)
        self._render_current_page()

    def _on_zoom_changed(self) -> None:
        self._zoom = float(self.zoom_combo.currentData())
        self._render_current_page()

    def _render_current_page(self) -> None:
        page = self._doc[self._current_page]
        self.canvas.set_page_data(
            page=page,
            page_index=self._current_page,
            page_count=self._page_count,
            zoom=self._zoom,
            rules=self.edited_rules,
            signature_dir=self._signature_dir,
        )
        self.prev_btn.setEnabled(self._current_page > 0)
        self.next_btn.setEnabled(self._current_page < self._page_count - 1)
        self._refresh_rule_list()
        self._load_rule_into_spins(self.rule_list.currentRow())

    def _rule_status_text(self, idx: int) -> str:
        t = self.i18n.t
        rule = self.edited_rules[idx]
        if not rule.get("enabled", True):
            return t("preview_status_disabled")
        if not page_matches(rule, self._current_page, self._page_count):
            return t("preview_status_page_skip")
        if str(rule.get("base", "text")).lower() == "coordinate":
            return t("preview_status_coord")
        anchor_r = self.canvas.anchor_rect_for(idx)
        if anchor_r is not None:
            return f"{t('preview_status_matched')} ({anchor_r.x0:.1f}, {anchor_r.y0:.1f})"
        return t("preview_status_unmatched")

    def _refresh_rule_list(self) -> None:
        current = self.rule_list.currentRow()
        self.rule_list.blockSignals(True)
        self.rule_list.clear()
        for idx, rule in enumerate(self.edited_rules):
            img = os.path.basename(str(rule.get("image", ""))) or "(no image)"
            anchor = str(rule.get("anchor", ""))
            label = f"#{idx + 1}  {img}"
            if str(rule.get("base", "text")).lower() == "text" and anchor:
                label += f"  [{anchor}]"
            item = QListWidgetItem(label)
            self.rule_list.addItem(item)
        if 0 <= current < len(self.edited_rules):
            self.rule_list.setCurrentRow(current)
        self.rule_list.blockSignals(False)

    def _load_rule_into_spins(self, idx: int) -> None:
        has_rule = 0 <= idx < len(self.edited_rules)
        for w in (self.base_combo, self.spin_x, self.spin_y, self.spin_w, self.spin_h):
            w.setEnabled(has_rule)
        if not has_rule:
            self.rule_status_lbl.setText("")
            return

        rule = self.edited_rules[idx]
        self._syncing_controls = True
        base_val = str(rule.get("base", "text")).lower()
        self.base_combo.setCurrentIndex(1 if base_val == "coordinate" else 0)
        self.spin_x.setValue(float(rule.get("offset_x", 0)))
        self.spin_y.setValue(float(rule.get("offset_y", 0)))
        self.spin_w.setValue(float(rule.get("width", 60)))
        self.spin_h.setValue(float(rule.get("height", 43)))
        self._syncing_controls = False

        self.rule_status_lbl.setText(self._rule_status_text(idx))
        self.canvas.set_selected_rule(idx)

    def _on_list_row_changed(self, row: int) -> None:
        self._load_rule_into_spins(row)

    def _on_canvas_rule_selected(self, idx: int) -> None:
        self.rule_list.setCurrentRow(idx)

    def _on_canvas_geometry_changed(self, idx: int) -> None:
        if idx == self.rule_list.currentRow():
            self._load_rule_into_spins(idx)

    def _on_spin_edited(self) -> None:
        if self._syncing_controls:
            return
        idx = self.rule_list.currentRow()
        if not (0 <= idx < len(self.edited_rules)):
            return
        rule = self.edited_rules[idx]
        prev_base = str(rule.get("base", "text")).lower()
        new_base = str(self.base_combo.currentData())

        rule["base"] = new_base
        rule["offset_x"] = round(self.spin_x.value(), 1)
        rule["offset_y"] = round(self.spin_y.value(), 1)
        rule["width"] = round(self.spin_w.value(), 1)
        rule["height"] = round(self.spin_h.value(), 1)

        if prev_base != new_base:
            self._render_current_page()
        else:
            self.rule_status_lbl.setText(self._rule_status_text(idx))
            self.canvas.update()

    def _on_cursor_moved(self, x: float, y: float) -> None:
        self.cursor_lbl.setText(self.i18n.t("preview_cursor_fmt", x=x, y=y))
