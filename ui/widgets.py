"""
ui/widgets.py  —  Todos os widgets customizados
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QDialog, QStackedWidget, QGraphicsOpacityEffect,
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF,
)
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QFont, QPen,
)


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════

def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()
        elif item.layout():
            clear_layout(item.layout())


# ══════════════════════════════════════════════════════════════════════════════
#  Card
# ══════════════════════════════════════════════════════════════════════════════

class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("card", "true")


# ══════════════════════════════════════════════════════════════════════════════
#  KPI Card  —  badge de texto curto (ex: "SAL", "REC") em vez de emoji
# ══════════════════════════════════════════════════════════════════════════════

class KPICard(Card):
    def __init__(self, title: str, value: str, subtitle: str = "",
                 badge: str = "?", color: str = "#5B8DEF", parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)
        self.setMinimumWidth(160)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(3)

        # topo: badge colorido
        top = QHBoxLayout()
        bdg = QLabel(badge[:3].upper())
        bdg.setFixedSize(38, 28)
        bdg.setAlignment(Qt.AlignCenter)
        bdg.setStyleSheet(
            f"background:{color}1A; color:{color};"
            "border-radius:7px; font-size:10px; font-weight:800;"
            "letter-spacing:0.5px;")
        top.addWidget(bdg)
        top.addStretch()
        lay.addLayout(top)

        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"color:{color}; font-size:20px; font-weight:800;")
        lay.addWidget(self._val)

        lbl = QLabel(title)
        lbl.setStyleSheet(
            "color:#64748B; font-size:11px; font-weight:600;")
        lay.addWidget(lbl)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color:#94A3B8; font-size:10px;")
            lay.addWidget(sub)

    def set_value(self, value: str, color: str = None):
        self._val.setText(value)
        if color:
            self._val.setStyleSheet(
                f"color:{color}; font-size:20px; font-weight:800;")


# ══════════════════════════════════════════════════════════════════════════════
#  Nav button (sidebar)
# ══════════════════════════════════════════════════════════════════════════════

class NavButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(f"   {text}", parent)
        self.setMinimumHeight(42)
        self.setCursor(Qt.PointingHandCursor)

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ══════════════════════════════════════════════════════════════════════════════
#  FadeStack
# ══════════════════════════════════════════════════════════════════════════════

class FadeStack(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animating = False

    def go(self, index: int):
        if index == self.currentIndex() or self._animating:
            return
        self._animating = True

        new_widget = self.widget(index)
        if new_widget is None:
            self._animating = False
            return

        fx_new = QGraphicsOpacityEffect(new_widget)
        fx_new.setOpacity(0.0)
        new_widget.setGraphicsEffect(fx_new)
        self.setCurrentIndex(index)

        anim_in = QPropertyAnimation(fx_new, b"opacity", self)
        anim_in.setDuration(250)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.OutCubic)

        def _done():
            new_widget.setGraphicsEffect(None)
            self._animating = False

        anim_in.finished.connect(_done)
        anim_in.start(QPropertyAnimation.DeleteWhenStopped)


# ══════════════════════════════════════════════════════════════════════════════
#  Donut Chart
# ══════════════════════════════════════════════════════════════════════════════

class DonutChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple] = []
        self.setMinimumSize(160, 160)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def set_data(self, data: list):
        self._data = [d for d in data if d[1] > 0]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if not p.isActive():
            return
        try:
            p.setRenderHint(QPainter.Antialiasing)

            total = sum(v for _, v, _ in self._data)
            if not self._data or total == 0:
                p.setPen(QColor("#94A3B8"))
                p.setFont(QFont("Segoe UI", 10))
                p.drawText(self.rect(), Qt.AlignCenter, "Sem dados")
                return

            W, H  = float(self.width()), float(self.height())
            size  = min(W, H) - 12.0
            x     = (W - size) / 2.0
            y     = (H - size) / 2.0
            outer = QRectF(x, y, size, size)

            angle = 90 * 16
            for _, value, color in self._data:
                span = int(value / total * 360 * 16)
                p.setBrush(QColor(color))
                p.setPen(Qt.NoPen)
                p.drawPie(outer, angle, -span)
                angle -= span

            hole = size * 0.52
            hx   = (W - hole) / 2.0
            hy   = (H - hole) / 2.0
            p.setBrush(QColor("#FFFFFF"))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(hx, hy, hole, hole))
        finally:
            p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  SmoothBar
# ══════════════════════════════════════════════════════════════════════════════

class SmoothBar(QWidget):
    def __init__(self, value: float = 0, max_val: float = 100,
                 color: str = "#5B8DEF", parent=None):
        super().__init__(parent)
        self._value  = 0.0
        self._target = min(float(value), float(max_val))
        self._max    = float(max_val) if max_val > 0 else 1.0
        self._color  = color
        self.setFixedHeight(7)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(16)

    def _step(self):
        diff = self._target - self._value
        if abs(diff) < 0.2:
            self._value = self._target
            self._timer.stop()
        else:
            self._value += diff * 0.14
        self.update()

    def set_value(self, val: float, max_val: float = None):
        if max_val is not None and max_val > 0:
            self._max = float(max_val)
        self._target = min(float(val), self._max)
        if not self._timer.isActive():
            self._timer.start(16)

    def paintEvent(self, event):
        p = QPainter(self)
        if not p.isActive():
            return
        try:
            p.setRenderHint(QPainter.Antialiasing)
            W = float(self.width())
            H = float(self.height())
            r = H / 2.0

            p.setBrush(QColor("#E8EDF7"))
            p.setPen(Qt.NoPen)
            bg = QPainterPath()
            bg.addRoundedRect(QRectF(0, 0, W, H), r, r)
            p.drawPath(bg)

            ratio  = max(0.0, min(self._value / self._max, 1.0))
            fill_w = ratio * W
            if fill_w > 0.5:
                p.setBrush(QColor(self._color))
                fg = QPainterPath()
                fg.addRoundedRect(QRectF(0, 0, fill_w, H), r, r)
                p.drawPath(fg)
        finally:
            p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  QuoteBar  — barra fixa de cotações (USD, EUR, BTC), sem emojis
# ══════════════════════════════════════════════════════════════════════════════

class _QuoteChip(QFrame):
    _COLORS = {"USD": "#16A34A", "EUR": "#3D74E8", "BTC": "#F59E0B"}

    def __init__(self, code: str, parent=None):
        super().__init__(parent)
        self.setObjectName("quoteChip")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(7)

        color = self._COLORS.get(code, "#64748B")

        badge = QLabel(code)
        badge.setFixedSize(34, 20)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background:{color}; color:#fff; border-radius:5px;"
            "font-size:9px; font-weight:800; letter-spacing:0.5px;"
            "border:none; background-color:" + color + ";")

        self._val = QLabel("—")
        self._val.setStyleSheet(
            "background:transparent; border:none;"
            "font-size:13px; font-weight:700; color:#1A1F36;")

        lay.addWidget(badge)
        lay.addWidget(self._val)

    def set_value(self, value: str):
        self._val.setText(value)


class QuoteBar(QFrame):
    _COINS = [
        ("USD", False),
        ("EUR", False),
        ("BTC", True),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quoteBar")
        self.setFixedHeight(48)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 0, 20, 0)
        outer.setSpacing(0)

        self._chips: dict[str, _QuoteChip] = {}
        for i, (code, _) in enumerate(self._COINS):
            chip = _QuoteChip(code)
            self._chips[code] = chip
            outer.addWidget(chip)

            if i < len(self._COINS) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.VLine)
                sep.setFixedHeight(18)
                sep.setStyleSheet(
                    "background:#DDE4F0; max-width:1px; margin:0 6px; border:none;")
                outer.addWidget(sep)

        outer.addStretch()

        self._upd = QLabel("Buscando cotacoes...")
        self._upd.setStyleSheet(
            "font-size:10px; color:#94A3B8; background:transparent; border:none;")
        outer.addWidget(self._upd)

    def update_quotes(self, quotes: dict, last_update: str):
        if not quotes:
            return
        for code, is_btc in self._COINS:
            if code in quotes:
                v   = quotes[code]
                fmt = f"R$ {v:,.0f}" if is_btc else f"R$ {v:,.3f}"
                self._chips[code].set_value(fmt)
        if last_update:
            self._upd.setText(f"Atualizado  {last_update}")


# ══════════════════════════════════════════════════════════════════════════════
#  BarChart
# ══════════════════════════════════════════════════════════════════════════════

class BarChart(QWidget):
    MONTHS = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
              "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple] = []
        self.setMinimumHeight(150)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def set_data(self, data: list):
        self._data = data
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if not p.isActive():
            return
        try:
            p.setRenderHint(QPainter.Antialiasing)

            if not self._data:
                p.setPen(QColor("#94A3B8"))
                p.setFont(QFont("Segoe UI", 10))
                p.drawText(self.rect(), Qt.AlignCenter, "Sem dados")
                return

            W   = float(self.width())
            H   = float(self.height())
            PAD = 20.0
            CH  = H - PAD * 2
            n   = len(self._data)
            max_v = max((v for _, v in self._data), default=1.0) or 1.0

            available = W - PAD * 2
            bar_w = max(available / (n * 1.9), 6.0)
            gap   = (available - bar_w * n) / max(n - 1, 1) if n > 1 else 0.0

            for i, (month, value) in enumerate(self._data):
                bh = (value / max_v) * CH * 0.88
                bx = PAD + i * (bar_w + gap)
                by = H - PAD - bh

                p.setBrush(QColor("#5B8DEF"))
                p.setPen(Qt.NoPen)
                path = QPainterPath()
                path.addRoundedRect(QRectF(bx, by, bar_w, bh), 3.0, 3.0)
                p.drawPath(path)

                p.setPen(QColor("#94A3B8"))
                p.setFont(QFont("Segoe UI", 8))
                try:
                    name = self.MONTHS[int(month)]
                except Exception:
                    name = str(month)
                p.drawText(int(bx - 1), int(H) - 3, name)
        finally:
            p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  LineChart
# ══════════════════════════════════════════════════════════════════════════════

class LineChart(QWidget):
    MONTHS = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
              "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._income:  list[tuple] = []
        self._expense: list[tuple] = []
        self.setMinimumHeight(210)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def set_data(self, income: list, expense: list):
        self._income  = income
        self._expense = expense
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if not p.isActive():
            return
        try:
            p.setRenderHint(QPainter.Antialiasing)

            W, H   = float(self.width()), float(self.height())
            PL, PR = 62.0, 16.0
            PT, PB = 22.0, 34.0

            all_vals = [v for _, v in self._income] + \
                       [v for _, v in self._expense]

            if not all_vals:
                p.setPen(QColor("#94A3B8"))
                p.setFont(QFont("Segoe UI", 10))
                p.drawText(self.rect(), Qt.AlignCenter, "Sem dados para exibir")
                return

            max_v = max(all_vals) * 1.15 or 1.0
            CW    = W - PL - PR
            CH    = H - PT - PB

            for i in range(5):
                gy  = PT + (i / 4.0) * CH
                val = max_v * (1.0 - i / 4.0)
                p.setPen(QPen(QColor("#E8EDF7"), 1, Qt.DashLine))
                p.drawLine(int(PL), int(gy), int(W - PR), int(gy))
                p.setPen(QColor("#94A3B8"))
                p.setFont(QFont("Segoe UI", 8))
                label = (f"{val/1000:.1f}k" if val >= 1000 else f"{val:.0f}")
                p.drawText(2, int(gy) + 5, label)

            def to_pts(series):
                n = len(series)
                if n == 0:
                    return []
                return [
                    (PL + (i / max(n - 1, 1)) * CW,
                     PT + (1.0 - v / max_v) * CH)
                    for i, (_, v) in enumerate(series)
                ]

            def draw_series(series, line_color: str):
                pts = to_pts(series)
                if len(pts) < 2:
                    return
                p.setPen(QPen(QColor(line_color), 2.5,
                              Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                path = QPainterPath()
                path.moveTo(pts[0][0], pts[0][1])
                for px, py in pts[1:]:
                    path.lineTo(px, py)
                p.setBrush(Qt.NoBrush)
                p.drawPath(path)

                p.setPen(QPen(QColor("#FFFFFF"), 2))
                p.setBrush(QColor(line_color))
                for px, py in pts:
                    p.drawEllipse(QRectF(px - 4, py - 4, 8.0, 8.0))

            draw_series(self._income,  "#22C55E")
            draw_series(self._expense, "#EF4444")

            ref = self._expense if self._expense else self._income
            if ref:
                n = len(ref)
                p.setPen(QColor("#64748B"))
                p.setFont(QFont("Segoe UI", 9))
                for i, (month, _) in enumerate(ref):
                    px = PL + (i / max(n - 1, 1)) * CW
                    try:
                        name = self.MONTHS[int(month)]
                    except Exception:
                        name = str(month)
                    p.drawText(int(px) - 13, int(H) - 4, name)

            for i, (color, label) in enumerate([
                ("#22C55E", "Receitas"),
                ("#EF4444", "Despesas"),
            ]):
                lx = int(PL) + i * 90
                p.setBrush(QColor(color))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(QRectF(lx, 6, 14, 8), 3, 3)
                p.setPen(QColor("#64748B"))
                p.setFont(QFont("Segoe UI", 9))
                p.drawText(lx + 18, 15, label)
        finally:
            p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  ConfirmDlg
# ══════════════════════════════════════════════════════════════════════════════

class ConfirmDlg(QDialog):
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(380, 165)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 18)
        lay.setSpacing(16)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size:14px; color:#1A1F36;")
        lay.addWidget(lbl)
        lay.addStretch()

        row = QHBoxLayout()
        bn  = QPushButton("Cancelar")
        bn.setProperty("role", "secondary")
        bn.clicked.connect(self.reject)
        by  = QPushButton("Confirmar")
        by.setProperty("role", "danger")
        by.clicked.connect(self.accept)
        row.addWidget(bn)
        row.addWidget(by)
        lay.addLayout(row)
