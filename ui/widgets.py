"""
ui/widgets.py  –  Todos os widgets customizados
Correções: sem QPainter aninhado, sem QGraphicsEffect durante paintEvent,
           FadeStack usa QStackedWidget real.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QDialog, QStackedWidget, QGraphicsOpacityEffect,
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF,
    QSequentialAnimationGroup, QParallelAnimationGroup,
)
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QFont, QPen,
)


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════

def clear_layout(layout):
    """Remove e deleta todos os itens de um layout."""
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()
        elif item.layout():
            clear_layout(item.layout())


# ══════════════════════════════════════════════════════════════════════════════
#  Card  (sem animação própria — evita conflito de painter)
# ══════════════════════════════════════════════════════════════════════════════

class Card(QFrame):
    """Card branco com borda arredondada. Sem efeito gráfico próprio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("card", "true")


# ══════════════════════════════════════════════════════════════════════════════
#  KPI Card
# ══════════════════════════════════════════════════════════════════════════════

class KPICard(Card):
    def __init__(self, title: str, value: str, subtitle: str = "",
                 icon: str = "💰", color: str = "#5B8DEF", parent=None):
        super().__init__(parent)
        self.setFixedHeight(118)
        self.setMinimumWidth(160)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(2)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 20))
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{color}; font-size:8px;")
        top.addWidget(icon_lbl)
        top.addStretch()
        top.addWidget(dot)
        lay.addLayout(top)

        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"color:{color}; font-size:19px; font-weight:700;")
        lay.addWidget(self._val)

        lbl = QLabel(title)
        lbl.setStyleSheet(
            "color:#7A849E; font-size:11px; font-weight:600;")
        lay.addWidget(lbl)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color:#A0AABF; font-size:10px;")
            lay.addWidget(sub)

        lay.addStretch()

    def set_value(self, value: str, color: str = None):
        self._val.setText(value)
        if color:
            self._val.setStyleSheet(
                f"color:{color}; font-size:19px; font-weight:700;")


# ══════════════════════════════════════════════════════════════════════════════
#  Nav button (sidebar)
# ══════════════════════════════════════════════════════════════════════════════

class NavButton(QPushButton):
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(f"  {icon}   {text}", parent)
        self.setMinimumHeight(44)
        self.setCursor(Qt.PointingHandCursor)

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ══════════════════════════════════════════════════════════════════════════════
#  FadeStack  — usa QStackedWidget + fade via QGraphicsOpacityEffect
#  A troca de página acontece FORA do paintEvent → sem conflito
# ══════════════════════════════════════════════════════════════════════════════

class FadeStack(QStackedWidget):
    """QStackedWidget com transição fade entre páginas."""

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

        # Prepara o novo widget com opacidade 0
        fx_new = QGraphicsOpacityEffect(new_widget)
        fx_new.setOpacity(0.0)
        new_widget.setGraphicsEffect(fx_new)

        # Mostra o novo widget (empilhado abaixo visualmente)
        self.setCurrentIndex(index)

        # Anima entrada (fade in)
        anim_in = QPropertyAnimation(fx_new, b"opacity", self)
        anim_in.setDuration(300)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.OutCubic)

        def _done():
            # Remove o efeito após animação para não interferir no painter
            new_widget.setGraphicsEffect(None)
            self._animating = False

        anim_in.finished.connect(_done)
        anim_in.start(QPropertyAnimation.DeleteWhenStopped)


# ══════════════════════════════════════════════════════════════════════════════
#  Donut Chart  — paintEvent único e seguro
# ══════════════════════════════════════════════════════════════════════════════

class DonutChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple] = []   # (label, value, color_hex)
        self.setMinimumSize(160, 160)
        # Desativa background automático do Qt para evitar double-paint
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, False)

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
                p.setPen(QColor("#A0AABF"))
                p.setFont(QFont("Segoe UI", 10))
                p.drawText(self.rect(), Qt.AlignCenter, "Sem dados")
                return

            W, H   = float(self.width()), float(self.height())
            size   = min(W, H) - 12.0
            x      = (W - size) / 2.0
            y      = (H - size) / 2.0
            outer  = QRectF(x, y, size, size)

            angle = 90 * 16
            for _, value, color in self._data:
                span = int(value / total * 360 * 16)
                p.setBrush(QColor(color))
                p.setPen(Qt.NoPen)
                p.drawPie(outer, angle, -span)
                angle -= span

            # buraco central
            hole  = size * 0.52
            hx    = (W - hole) / 2.0
            hy    = (H - hole) / 2.0
            p.setBrush(QColor("#FFFFFF"))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(hx, hy, hole, hole))
        finally:
            p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  SmoothBar  — barra de progresso animada, paintEvent único
# ══════════════════════════════════════════════════════════════════════════════

class SmoothBar(QWidget):
    def __init__(self, value: float = 0, max_val: float = 100,
                 color: str = "#5B8DEF", parent=None):
        super().__init__(parent)
        self._value  = 0.0
        self._target = min(float(value), float(max_val))
        self._max    = float(max_val) if max_val > 0 else 1.0
        self._color  = color
        self.setFixedHeight(8)
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

            # fundo
            p.setBrush(QColor("#E8EDF7"))
            p.setPen(Qt.NoPen)
            bg = QPainterPath()
            bg.addRoundedRect(QRectF(0, 0, W, H), r, r)
            p.drawPath(bg)

            # preenchimento
            ratio    = max(0.0, min(self._value / self._max, 1.0))
            fill_w   = ratio * W
            if fill_w > 0.5:
                p.setBrush(QColor(self._color))
                fg = QPainterPath()
                fg.addRoundedRect(QRectF(0, 0, fill_w, H), r, r)
                p.drawPath(fg)
        finally:
            p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  TickerBar  — cotações em scroll, paintEvent único
# ══════════════════════════════════════════════════════════════════════════════

class TickerBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self._text  = "   Conectando e buscando cotações…   "
        self._x     = 0.0
        self._tw    = 0   # text width em pixels (calculado no primeiro paint)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(18)   # ~55 fps

    def update_quotes(self, quotes: dict, last_update: str):
        if not quotes:
            return
        sym = {"USD": "🇺🇸 USD", "EUR": "🇪🇺 EUR",
               "GBP": "🇬🇧 GBP", "BTC": "₿ BTC"}
        parts = []
        for k, label in sym.items():
            if k in quotes:
                v   = quotes[k]
                fmt = f"R$ {v:,.0f}" if k == "BTC" else f"R$ {v:,.3f}"
                parts.append(f"  {label}  {fmt}  ·")
        self._text = "      ".join(parts)
        if last_update:
            self._text += f"      ⟳ {last_update}"
        self._tw = 0        # força recálculo
        self._x  = float(self.width())

    def _tick(self):
        self._x -= 0.9
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if not p.isActive():
            return
        try:
            p.fillRect(self.rect(), QColor("#EBF2FF"))

            font = QFont("Segoe UI", 10)
            font.setWeight(QFont.Medium)
            p.setFont(font)
            fm = p.fontMetrics()

            if self._tw == 0:
                self._tw = fm.horizontalAdvance(self._text) + 60

            if self._x + self._tw < 0:
                self._x = float(self.width())

            p.setPen(QColor("#2D5BE3"))
            p.drawText(int(self._x), 21, self._text)

            # loop contínuo
            if self._x < self.width():
                p.drawText(int(self._x + self._tw), 21, self._text)
        finally:
            p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  BarChart  — paintEvent único
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
                p.setPen(QColor("#A0AABF"))
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

                # barra
                p.setBrush(QColor("#5B8DEF"))
                p.setPen(Qt.NoPen)
                path = QPainterPath()
                path.addRoundedRect(QRectF(bx, by, bar_w, bh), 3.0, 3.0)
                p.drawPath(path)

                # rótulo mês
                p.setPen(QColor("#A0AABF"))
                p.setFont(QFont("Segoe UI", 8))
                try:
                    name = self.MONTHS[int(month)]
                except Exception:
                    name = str(month)
                p.drawText(int(bx - 1), int(H) - 3, name)
        finally:
            p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  LineChart  — paintEvent único
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

            W, H    = float(self.width()), float(self.height())
            PL, PR  = 62.0, 16.0
            PT, PB  = 22.0, 34.0

            all_vals = [v for _, v in self._income] + \
                       [v for _, v in self._expense]

            if not all_vals:
                p.setPen(QColor("#A0AABF"))
                p.setFont(QFont("Segoe UI", 10))
                p.drawText(self.rect(), Qt.AlignCenter,
                           "Sem dados para exibir")
                return

            max_v = max(all_vals) * 1.15 or 1.0
            CW    = W - PL - PR
            CH    = H - PT - PB

            # ── grid horizontal ──
            for i in range(5):
                gy  = PT + (i / 4.0) * CH
                val = max_v * (1.0 - i / 4.0)
                p.setPen(QPen(QColor("#E8EDF7"), 1, Qt.DashLine))
                p.drawLine(int(PL), int(gy), int(W - PR), int(gy))
                p.setPen(QColor("#B0BAD0"))
                p.setFont(QFont("Segoe UI", 8))
                label = (f"{val/1000:.1f}k" if val >= 1000
                         else f"{val:.0f}")
                p.drawText(2, int(gy) + 5, label)

            # ── helper: converte série em lista de (x,y) ──
            def to_pts(series):
                n = len(series)
                if n == 0:
                    return []
                return [
                    (PL + (i / max(n - 1, 1)) * CW,
                     PT + (1.0 - v / max_v) * CH)
                    for i, (_, v) in enumerate(series)
                ]

            # ── desenha uma série ──
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

                # pontos
                p.setPen(QPen(QColor("#FFFFFF"), 2))
                p.setBrush(QColor(line_color))
                for px, py in pts:
                    p.drawEllipse(QRectF(px - 4.5, py - 4.5, 9.0, 9.0))

            draw_series(self._income,  "#22C55E")
            draw_series(self._expense, "#EF4444")

            # ── rótulos eixo X ──
            ref = self._expense if self._expense else self._income
            if ref:
                n = len(ref)
                p.setPen(QColor("#7A849E"))
                p.setFont(QFont("Segoe UI", 9))
                for i, (month, _) in enumerate(ref):
                    px = PL + (i / max(n - 1, 1)) * CW
                    try:
                        name = self.MONTHS[int(month)]
                    except Exception:
                        name = str(month)
                    p.drawText(int(px) - 13, int(H) - 4, name)

            # ── legenda ──
            for i, (color, label) in enumerate([
                ("#22C55E", "Receitas"),
                ("#EF4444", "Despesas"),
            ]):
                lx = int(PL) + i * 90
                p.setBrush(QColor(color))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(QRectF(lx, 6, 14, 8), 3, 3)
                p.setPen(QColor("#7A849E"))
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
        bn = QPushButton("Cancelar")
        bn.setProperty("role", "secondary")
        bn.clicked.connect(self.reject)
        by = QPushButton("Confirmar")
        by.setProperty("role", "danger")
        by.clicked.connect(self.accept)
        row.addWidget(bn)
        row.addWidget(by)
        lay.addLayout(row)