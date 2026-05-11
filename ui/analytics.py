from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame, QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime

import database as db
from ui.widgets import Card, DonutChart, LineChart, SmoothBar, clear_layout

MONTHS_PT = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


class CompareBar(QWidget):
    def __init__(self, label: str, curr: float,
                 prev: float, color: str = "#5B8DEF", parent=None):
        super().__init__(parent)
        self.setFixedHeight(68)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(3)

        diff  = curr - prev
        pct   = (diff / prev * 100) if prev > 0 else 0.0
        arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
        dc    = ("#EF4444" if diff > 0
                 else "#16A34A" if diff < 0
                 else "#9CA3AF")

        hdr = QHBoxLayout()
        l1 = QLabel(label)
        l1.setStyleSheet(
            "font-size:12px; color:#7A849E; font-weight:600;")
        l2 = QLabel(f"{arrow} {abs(pct):.1f}%")
        l2.setStyleSheet(
            f"font-size:11px; color:{dc}; font-weight:700;")
        l3 = QLabel(f"R$ {curr:,.0f}")
        l3.setStyleSheet(
            f"font-size:13px; color:{color}; font-weight:700;")
        hdr.addWidget(l1)
        hdr.addStretch()
        hdr.addWidget(l2)
        hdr.addWidget(l3)
        lay.addLayout(hdr)

        bar = SmoothBar(curr, max(curr, prev, 1), color)
        lay.addWidget(bar)

        pl = QLabel(f"Mês anterior: R$ {prev:,.0f}")
        pl.setStyleSheet("font-size:10px; color:#A0AABF;")
        lay.addWidget(pl)


class AnalyticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._year  = datetime.now().year
        self._month = datetime.now().month
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 20)
        lay.setSpacing(14)

        # cabeçalho
        hdr = QHBoxLayout()
        t = QLabel("Analytics & BI")
        t.setStyleSheet(
            "font-size:22px; font-weight:700; color:#1A1F36;")
        hdr.addWidget(t)
        hdr.addStretch()

        self._ycb = QComboBox()
        cy = datetime.now().year
        for yy in range(cy - 3, cy + 1):
            self._ycb.addItem(str(yy), yy)
        self._ycb.setCurrentIndex(3)
        self._ycb.setFixedHeight(36)
        self._ycb.currentIndexChanged.connect(self._year_changed)
        hdr.addWidget(self._ycb)
        lay.addLayout(hdr)

        # scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self._lay = QVBoxLayout(inner)
        self._lay.setSpacing(14)
        self._lay.setContentsMargins(0, 0, 6, 0)
        scroll.setWidget(inner)
        lay.addWidget(scroll)

        # ── linha anual ──
        lc = Card()
        ll = QVBoxLayout(lc)
        ll.setContentsMargins(16, 14, 16, 12)
        ll.addWidget(self._sec("📈  Receitas vs Despesas — Ano Completo"))
        self._line = LineChart()
        ll.addWidget(self._line)
        self._lay.addWidget(lc)

        # ── comparativo mensal ──
        mc = Card()
        ml = QVBoxLayout(mc)
        ml.setContentsMargins(16, 14, 16, 12)
        ml.addWidget(self._sec("📊  Comparativo Mensal"))

        msel = QHBoxLayout()
        self._mcb = QComboBox()
        _months = [
            "Janeiro", "Fevereiro", "Março", "Abril",
            "Maio", "Junho", "Julho", "Agosto",
            "Setembro", "Outubro", "Novembro", "Dezembro",
        ]
        for i, mn in enumerate(_months):
            self._mcb.addItem(mn, i + 1)
        self._mcb.setCurrentIndex(self._month - 1)
        self._mcb.setFixedHeight(36)
        self._mcb.setFixedWidth(165)
        self._mcb.currentIndexChanged.connect(self._month_changed)
        msel.addWidget(self._mcb)
        msel.addStretch()
        ml.addLayout(msel)

        self._cmp_lay = QVBoxLayout()
        self._cmp_lay.setSpacing(8)
        ml.addLayout(self._cmp_lay)
        self._lay.addWidget(mc)

        # ── donut + breakdown ──
        cr = QHBoxLayout()
        cr.setSpacing(14)

        dc = Card()
        dl = QVBoxLayout(dc)
        dl.setContentsMargins(16, 14, 16, 12)
        dl.addWidget(self._sec("🍩  Despesas por Categoria"))
        self._donut = DonutChart()
        self._donut.setMinimumHeight(200)
        dl.addWidget(self._donut)
        cr.addWidget(dc, 1)

        bkc = Card()
        bkl = QVBoxLayout(bkc)
        bkl.setContentsMargins(16, 14, 16, 12)
        bkl.addWidget(self._sec("📋  Detalhamento"))
        self._bk_lay = QVBoxLayout()
        self._bk_lay.setSpacing(8)
        bkl.addLayout(self._bk_lay)
        bkl.addStretch()
        cr.addWidget(bkc, 1)
        self._lay.addLayout(cr)

        self._lay.addStretch()

    @staticmethod
    def _sec(text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(
            "font-size:14px; font-weight:700; color:#1A1F36;"
            "margin-bottom:4px;")
        return l

    def _year_changed(self):
        self._year = self._ycb.currentData()
        self.refresh()

    def _month_changed(self):
        self._month = self._mcb.currentData()
        self._refresh_cmp()
        self._refresh_cats()

    def refresh(self):
        summary = db.get_monthly_summary(self._year)
        monthly: dict = {}
        for row in summary:
            mn = row["month"]
            monthly.setdefault(mn, {"income": 0.0, "expense": 0.0})
            monthly[mn][row["type"]] = row["total"]

        self._line.set_data(
            [(mn, v["income"])  for mn, v in sorted(monthly.items())],
            [(mn, v["expense"]) for mn, v in sorted(monthly.items())],
        )
        self._refresh_cmp()
        self._refresh_cats()

    def _refresh_cmp(self):
        clear_layout(self._cmp_lay)
        m, y  = self._month, self._year
        pm    = m - 1 if m > 1 else 12
        py    = y if m > 1 else y - 1
        curr  = db.get_transactions(m, y)
        prev  = db.get_transactions(pm, py)
        ci    = sum(t["amount"] for t in curr if t["type"] == "income")
        ce    = sum(t["amount"] for t in curr if t["type"] == "expense")
        pi    = sum(t["amount"] for t in prev if t["type"] == "income")
        pe    = sum(t["amount"] for t in prev if t["type"] == "expense")
        for lbl, cv, pv, col in [
            ("💰  Receitas", ci, pi, "#16A34A"),
            ("💸  Despesas", ce, pe, "#EF4444"),
            ("💎  Saldo",    ci - ce, pi - pe, "#3D74E8"),
        ]:
            self._cmp_lay.addWidget(CompareBar(lbl, cv, pv, col))

    def _refresh_cats(self):
        clear_layout(self._bk_lay)
        cats  = db.get_category_breakdown(self._month, self._year)
        total = sum(r["total"] for r in cats) or 1.0

        if cats:
            self._donut.set_data(
                [(r["name"], r["total"], r["color"]) for r in cats])
            for r in cats:
                pct = r["total"] / total * 100
                vl  = QVBoxLayout()
                vl.setSpacing(2)
                hr  = QHBoxLayout()
                nl  = QLabel(f"{r['icon']}  {r['name']}")
                nl.setStyleSheet("font-size:11px; color:#1A1F36;")
                pl  = QLabel(f"{pct:.1f}%  ·  R$ {r['total']:,.0f}")
                pl.setStyleSheet(
                    f"font-size:11px; color:{r['color']};"
                    "font-weight:700;")
                pl.setAlignment(Qt.AlignRight)
                hr.addWidget(nl)
                hr.addStretch()
                hr.addWidget(pl)
                vl.addLayout(hr)
                bar = SmoothBar(pct, 100, r["color"])
                vl.addWidget(bar)
                self._bk_lay.addLayout(vl)
        else:
            self._donut.set_data([])
            e = QLabel("Sem dados neste período")
            e.setStyleSheet("color:#A0AABF; padding:8px;")
            self._bk_lay.addWidget(e)