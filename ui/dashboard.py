from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt
from datetime import datetime

import database as db
from ui.widgets import Card, KPICard, BarChart, DonutChart, clear_layout

MONTHS_PT = [
    "", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _badge(name: str, color: str) -> QLabel:
    txt = (name or "?")[:2].upper()
    lbl = QLabel(txt)
    lbl.setFixedSize(32, 32)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"background:{color}22; color:{color}; border-radius:9px;"
        "font-size:10px; font-weight:800; border:none;")
    return lbl


class _TxRow(QFrame):
    def __init__(self, tx, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(12)

        cat_color = tx["category_color"] or "#94A3B8"
        cat_name  = tx["category_name"] or "?"
        lay.addWidget(_badge(cat_name, cat_color))

        info = QVBoxLayout()
        info.setSpacing(1)
        d = QLabel(tx["description"])
        d.setStyleSheet("font-size:13px; font-weight:600; color:#1A1F36;")
        c = QLabel(tx["category_name"] or "—")
        c.setStyleSheet("font-size:10px; color:#94A3B8;")
        info.addWidget(d)
        info.addWidget(c)
        lay.addLayout(info)
        lay.addStretch()

        is_inc = tx["type"] == "income"
        color  = "#16A34A" if is_inc else "#DC2626"
        sign   = "+" if is_inc else "-"

        vr = QVBoxLayout()
        vr.setSpacing(1)
        a = QLabel(f"{sign} R$ {float(tx['amount']):,.2f}")
        a.setStyleSheet(f"color:{color}; font-weight:700; font-size:13px;")
        dt = QLabel(tx["date"])
        dt.setStyleSheet("color:#94A3B8; font-size:10px;")
        dt.setAlignment(Qt.AlignRight)
        vr.addWidget(a)
        vr.addWidget(dt)
        lay.addLayout(vr)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 20)
        root.setSpacing(18)

        hdr = QHBoxLayout()
        t = QLabel("Dashboard")
        t.setStyleSheet("font-size:22px; font-weight:800; color:#1A1F36;")
        self._date_lbl = QLabel()
        self._date_lbl.setStyleSheet("color:#64748B; font-size:13px;")
        hdr.addWidget(t)
        hdr.addStretch()
        hdr.addWidget(self._date_lbl)
        root.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self._lay = QVBoxLayout(inner)
        self._lay.setSpacing(18)
        self._lay.setContentsMargins(0, 0, 6, 0)
        scroll.setWidget(inner)
        root.addWidget(scroll)

        self._kpi_row = QHBoxLayout()
        self._kpi_row.setSpacing(12)
        self._lay.addLayout(self._kpi_row)

        charts = QHBoxLayout()
        charts.setSpacing(14)

        bar_card = Card()
        bar_card.setMinimumHeight(200)
        bl = QVBoxLayout(bar_card)
        bl.setContentsMargins(16, 14, 16, 12)
        bl.addWidget(self._sec("Gastos Mensais"))
        self._bar = BarChart()
        bl.addWidget(self._bar)
        charts.addWidget(bar_card, 2)

        donut_card = Card()
        donut_card.setMinimumHeight(200)
        dl = QVBoxLayout(donut_card)
        dl.setContentsMargins(16, 14, 16, 12)
        dl.addWidget(self._sec("Categorias"))
        self._donut = DonutChart()
        dl.addWidget(self._donut)
        self._legend = QVBoxLayout()
        self._legend.setSpacing(3)
        dl.addLayout(self._legend)
        charts.addWidget(donut_card, 1)
        self._lay.addLayout(charts)

        rc = Card()
        rl = QVBoxLayout(rc)
        rl.setContentsMargins(16, 14, 16, 12)
        rl.addWidget(self._sec("Transacoes Recentes"))
        self._recent_lay = QVBoxLayout()
        self._recent_lay.setSpacing(0)
        rl.addLayout(self._recent_lay)
        self._lay.addWidget(rc)

        sc = Card()
        sl = QVBoxLayout(sc)
        sl.setContentsMargins(16, 14, 16, 12)
        sl.addWidget(self._sec("Assinaturas Ativas"))
        self._sub_lay = QVBoxLayout()
        self._sub_lay.setSpacing(6)
        sl.addLayout(self._sub_lay)
        self._lay.addWidget(sc)

        self._lay.addStretch()

    @staticmethod
    def _sec(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size:13px; font-weight:700; color:#1A1F36; margin-bottom:4px;")
        return lbl

    def refresh(self):
        now = datetime.now()
        self._date_lbl.setText(
            now.strftime("%A, %d de %B de %Y").capitalize())

        m, y    = now.month, now.year
        txs     = db.get_transactions(m, y)
        income  = sum(t["amount"] for t in txs if t["type"] == "income")
        expense = sum(t["amount"] for t in txs if t["type"] == "expense")
        balance = income - expense

        pm  = m - 1 if m > 1 else 12
        py  = y if m > 1 else y - 1
        prev     = db.get_transactions(pm, py)
        prev_exp = sum(t["amount"] for t in prev if t["type"] == "expense")
        dp       = ((expense - prev_exp) / prev_exp * 100) if prev_exp else 0
        diff_str = f"{'alta' if dp > 0 else 'queda'} de {abs(dp):.1f}% vs mes anterior"

        subs      = db.get_subscriptions()
        sub_total = sum(s["amount"] for s in subs if s["active"])
        sub_count = sum(1 for s in subs if s["active"])

        # KPIs
        clear_layout(self._kpi_row)
        bc = "#3D74E8" if balance >= 0 else "#DC2626"
        for title, val, sub, badge, color in [
            ("Saldo do Mes",  f"R$ {balance:,.2f}", MONTHS_PT[m],          "SAL", bc),
            ("Receitas",      f"R$ {income:,.2f}",
             f"{sum(1 for t in txs if t['type']=='income')} transacoes",   "REC", "#16A34A"),
            ("Despesas",      f"R$ {expense:,.2f}", diff_str,               "DES", "#DC2626"),
            ("Assinaturas",   f"R$ {sub_total:,.2f}",
             f"{sub_count} ativas",                                         "ASS", "#F59E0B"),
        ]:
            self._kpi_row.addWidget(
                KPICard(title, val, sub, badge, color))

        # Barra mensal
        summary = db.get_monthly_summary(y)
        monthly: dict = {}
        for row in summary:
            mn = row["month"]
            monthly.setdefault(mn, {"income": 0.0, "expense": 0.0})
            monthly[mn][row["type"]] = row["total"]
        self._bar.set_data(
            [(mn, v["expense"]) for mn, v in sorted(monthly.items())])

        # Donut
        clear_layout(self._legend)
        cats = db.get_category_breakdown(m, y)
        if cats:
            self._donut.set_data(
                [(r["name"], r["total"], r["color"]) for r in cats])
            tot = sum(r["total"] for r in cats) or 1
            for r in cats[:5]:
                pct   = r["total"] / tot * 100
                row_w = QHBoxLayout()
                dot   = QLabel("●")
                dot.setStyleSheet(f"color:{r['color']}; font-size:9px;")
                dot.setFixedWidth(16)
                nm = QLabel(r["name"])
                nm.setStyleSheet("font-size:11px;")
                vl = QLabel(f"R$ {r['total']:,.0f}  ({pct:.0f}%)")
                vl.setStyleSheet("font-size:11px; color:#94A3B8;")
                vl.setAlignment(Qt.AlignRight)
                row_w.addWidget(dot)
                row_w.addWidget(nm)
                row_w.addStretch()
                row_w.addWidget(vl)
                self._legend.addLayout(row_w)
        else:
            self._donut.set_data([])

        # Recentes
        clear_layout(self._recent_lay)
        recent = db.get_transactions(limit=8)
        if recent:
            for tx in recent:
                self._recent_lay.addWidget(_TxRow(tx))
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet("background:#F0F4FF; max-height:1px;")
                self._recent_lay.addWidget(sep)
        else:
            e = QLabel("Nenhuma transacao ainda")
            e.setStyleSheet("color:#94A3B8; padding:16px;")
            e.setAlignment(Qt.AlignCenter)
            self._recent_lay.addWidget(e)

        # Assinaturas
        clear_layout(self._sub_lay)
        active_subs = [s for s in subs if s["active"]]
        if active_subs:
            for s in active_subs[:6]:
                row_w  = QHBoxLayout()
                color  = s["color"] or "#5B8DEF"
                row_w.addWidget(_badge(s["name"], color))

                info_v = QVBoxLayout()
                info_v.setSpacing(1)
                nm = QLabel(s["name"])
                nm.setStyleSheet("font-size:13px; font-weight:600; color:#1A1F36;")
                dy = QLabel(f"Dia {s['billing_day']}")
                dy.setStyleSheet("font-size:10px; color:#94A3B8;")
                info_v.addWidget(nm)
                info_v.addWidget(dy)
                vl = QLabel(f"R$ {s['amount']:,.2f}")
                vl.setStyleSheet(
                    f"color:{color}; font-weight:700; font-size:13px;")
                row_w.addLayout(info_v)
                row_w.addStretch()
                row_w.addWidget(vl)
                self._sub_lay.addLayout(row_w)
        else:
            e = QLabel("Nenhuma assinatura ativa")
            e.setStyleSheet("color:#94A3B8;")
            self._sub_lay.addWidget(e)
