from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea,
)
from PySide6.QtCore import Qt
from datetime import datetime

import database as db
from ui.widgets import Card, KPICard, SmoothBar, clear_layout

MONTHS_PT = [
    "", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _badge(text: str, color: str, bg: str = None, size: int = 32) -> QLabel:
    lbl = QLabel(text)
    lbl.setFixedHeight(size)
    lbl.setMinimumWidth(size)
    lbl.setAlignment(Qt.AlignCenter)
    bg_color = bg or f"{color}22"
    lbl.setStyleSheet(
        f"background:{bg_color}; color:{color}; border-radius:{size // 4}px;"
        f"font-size:10px; font-weight:800; padding:2px 6px; border:none;")
    return lbl


class InvoicePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        now = datetime.now()
        self._month = now.month
        self._year  = now.year
        self._build()
        self.refresh()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 20)
        lay.setSpacing(14)

        # header: title + nav
        hdr = QHBoxLayout()
        t = QLabel("Simulador de Fatura")
        t.setStyleSheet("font-size:22px; font-weight:800; color:#1A1F36;")
        hdr.addWidget(t)
        hdr.addStretch()

        self._prev_btn = QPushButton("<")
        self._prev_btn.setFixedSize(36, 36)
        self._prev_btn.setCursor(Qt.PointingHandCursor)
        self._prev_btn.setStyleSheet(
            "background:#EEF4FF; color:#3D74E8; border-radius:8px;"
            "font-size:14px; font-weight:700; border:none;")
        self._prev_btn.clicked.connect(self._prev_month)

        self._month_lbl = QLabel()
        self._month_lbl.setFixedWidth(160)
        self._month_lbl.setAlignment(Qt.AlignCenter)
        self._month_lbl.setStyleSheet(
            "font-size:14px; font-weight:700; color:#1A1F36;")

        self._next_btn = QPushButton(">")
        self._next_btn.setFixedSize(36, 36)
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.setStyleSheet(
            "background:#EEF4FF; color:#3D74E8; border-radius:8px;"
            "font-size:14px; font-weight:700; border:none;")
        self._next_btn.clicked.connect(self._next_month)

        hdr.addWidget(self._prev_btn)
        hdr.addWidget(self._month_lbl)
        hdr.addWidget(self._next_btn)
        lay.addLayout(hdr)

        # KPI row
        self._kpi_row = QHBoxLayout()
        self._kpi_row.setSpacing(12)
        lay.addLayout(self._kpi_row)

        # scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self._content = QVBoxLayout(inner)
        self._content.setSpacing(14)
        self._content.setContentsMargins(0, 0, 6, 0)
        scroll.setWidget(inner)
        lay.addWidget(scroll)

    # ── navigation ────────────────────────────────────────────────────────────

    def _prev_month(self):
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self.refresh()

    def _next_month(self):
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self.refresh()

    # ── refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        self._month_lbl.setText(f"{MONTHS_PT[self._month]} {self._year}")
        self._refresh_kpis()
        self._refresh_content()

    def _refresh_kpis(self):
        clear_layout(self._kpi_row)
        txs     = db.get_invoice_transactions(self._month, self._year)
        total   = sum(float(t["amount"]) for t in txs)
        count   = len(txs)
        parc    = sum(1 for t in txs if t["installment_total"] and t["installment_total"] > 0)

        for lbl, val, col, badge in [
            ("Total Fatura",  f"R$ {total:,.2f}", "#EF4444", "FAT"),
            ("Lancamentos",   str(count),          "#3D74E8", "LAN"),
            ("Parcelados",    str(parc),            "#D97706", "PAR"),
        ]:
            kpi = KPICard(lbl, val, "", badge, col)
            kpi.setFixedHeight(96)
            self._kpi_row.addWidget(kpi)

    def _refresh_content(self):
        clear_layout(self._content)

        # ── transactions list ─────────────────────────────────────────────────
        txs = db.get_invoice_transactions(self._month, self._year)

        tx_card = Card()
        tx_lay  = QVBoxLayout(tx_card)
        tx_lay.setContentsMargins(16, 14, 16, 14)
        tx_lay.setSpacing(6)

        sec = QLabel(f"Lancamentos de {MONTHS_PT[self._month]}")
        sec.setStyleSheet(
            "font-size:13px; font-weight:700; color:#1A1F36; margin-bottom:4px;")
        tx_lay.addWidget(sec)

        if not txs:
            empty = QLabel("Nenhuma despesa neste mes.")
            empty.setStyleSheet("color:#94A3B8; font-size:12px; padding:8px;")
            tx_lay.addWidget(empty)
        else:
            for t in txs:
                tx_lay.addWidget(self._make_tx_row(t))

        self._content.addWidget(tx_card)

        # ── 6-month projection ────────────────────────────────────────────────
        proj = db.get_installment_projection(self._year, self._month, 6)
        max_total = max((p[2] for p in proj), default=1.0) or 1.0

        proj_card = Card()
        pr_lay    = QVBoxLayout(proj_card)
        pr_lay.setContentsMargins(16, 14, 16, 14)
        pr_lay.setSpacing(8)

        sec2 = QLabel("Comprometimento com Parcelas — Proximos 6 Meses")
        sec2.setStyleSheet(
            "font-size:13px; font-weight:700; color:#1A1F36; margin-bottom:4px;")
        pr_lay.addWidget(sec2)

        has_any = any(p[2] > 0 for p in proj)
        if not has_any:
            empty2 = QLabel("Nenhum parcelamento ativo.")
            empty2.setStyleSheet("color:#94A3B8; font-size:12px; padding:8px;")
            pr_lay.addWidget(empty2)
        else:
            for y, m, total in proj:
                pr_lay.addWidget(
                    self._make_proj_row(y, m, total, max_total,
                                        y == self._year and m == self._month))

        self._content.addWidget(proj_card)

        # ── active installment groups ─────────────────────────────────────────
        groups = db.get_active_installment_groups()

        gr_card = Card()
        gr_lay  = QVBoxLayout(gr_card)
        gr_lay.setContentsMargins(16, 14, 16, 14)
        gr_lay.setSpacing(6)

        sec3 = QLabel("Parcelamentos Ativos")
        sec3.setStyleSheet(
            "font-size:13px; font-weight:700; color:#1A1F36; margin-bottom:4px;")
        gr_lay.addWidget(sec3)

        if not groups:
            empty3 = QLabel("Nenhum parcelamento ativo no momento.")
            empty3.setStyleSheet("color:#94A3B8; font-size:12px; padding:8px;")
            gr_lay.addWidget(empty3)
        else:
            for g in groups:
                gr_lay.addWidget(self._make_group_row(g))

        self._content.addWidget(gr_card)
        self._content.addStretch()

    # ── row builders ──────────────────────────────────────────────────────────

    def _make_tx_row(self, t) -> QWidget:
        row = QWidget()
        row.setFixedHeight(46)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(10)

        # category badge
        cat_name  = (t["category_name"] or "?")[:2].upper()
        cat_color = t["category_color"] or "#5B8DEF"
        lay.addWidget(_badge(cat_name, cat_color))

        # description
        desc = QLabel(t["description"])
        desc.setStyleSheet("font-size:12px; color:#1A1F36; font-weight:600;")
        lay.addWidget(desc, 1)

        # installment badge
        inst_total = t["installment_total"] if t["installment_total"] else 0
        if inst_total > 0:
            lbl = _badge(
                f"{t['installment_current']}/{inst_total}",
                "#D97706", "#FEF3C7")
            lay.addWidget(lbl)

        # date
        try:
            d = datetime.strptime(t["date"], "%Y-%m-%d")
            date_txt = d.strftime("%d/%m")
        except Exception:
            date_txt = t["date"]
        dl = QLabel(date_txt)
        dl.setStyleSheet("font-size:11px; color:#94A3B8;")
        dl.setFixedWidth(40)
        dl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(dl)

        # amount
        al = QLabel(f"R$ {float(t['amount']):,.2f}")
        al.setStyleSheet("font-size:13px; font-weight:700; color:#EF4444;")
        al.setFixedWidth(100)
        al.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(al)

        # separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#F1F5F9; max-height:1px;")

        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)
        vl.addWidget(row)
        vl.addWidget(sep)
        return w

    def _make_proj_row(self, y: int, m: int, total: float,
                       max_total: float, is_current: bool) -> QWidget:
        w   = QWidget()
        w.setFixedHeight(52)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(3)

        hdr = QHBoxLayout()
        color = "#3D74E8" if is_current else "#64748B"
        ml = QLabel(f"{MONTHS_PT[m][:3]} {y}")
        ml.setStyleSheet(
            f"font-size:12px; font-weight:{'700' if is_current else '500'};"
            f"color:{color};")
        vl = QLabel(f"R$ {total:,.0f}")
        vl.setStyleSheet(
            f"font-size:12px; font-weight:700; color:{color};")
        vl.setAlignment(Qt.AlignRight)
        hdr.addWidget(ml)
        hdr.addStretch()
        hdr.addWidget(vl)
        lay.addLayout(hdr)

        bar = SmoothBar(total, max_total or 1, "#3D74E8" if is_current else "#94A3B8")
        lay.addWidget(bar)
        return w

    def _make_group_row(self, g) -> QWidget:
        color = g["category_color"] or "#5B8DEF"

        row = QFrame()
        row.setFixedHeight(70)
        row.setStyleSheet(
            "background:#FAFBFD; border-radius:10px;")

        outer = QHBoxLayout(row)
        outer.setContentsMargins(0, 0, 12, 0)
        outer.setSpacing(12)

        stripe = QFrame()
        stripe.setFixedWidth(5)
        stripe.setStyleSheet(
            f"background:{color}; border-top-left-radius:10px;"
            "border-bottom-left-radius:10px;")
        outer.addWidget(stripe)

        paid      = int(g["paid_count"])
        total_p   = int(g["installment_total"])
        remaining = int(g["remaining_count"])
        rem_total = float(g["remaining_total"])
        monthly   = float(g["monthly_amount"])

        info = QVBoxLayout()
        info.setSpacing(2)
        nm = QLabel(g["description"])
        nm.setStyleSheet("font-size:13px; font-weight:700; color:#1A1F36;")
        pr = QLabel(f"{paid} de {total_p} pagas  —  {remaining} restantes")
        pr.setStyleSheet("font-size:10px; color:#64748B;")
        info.addWidget(nm)
        info.addWidget(pr)
        outer.addLayout(info, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        mv = QLabel(f"R$ {monthly:,.2f}/mes")
        mv.setStyleSheet(f"font-size:13px; font-weight:700; color:{color};")
        mv.setAlignment(Qt.AlignRight)
        rv = QLabel(f"Restam R$ {rem_total:,.2f}")
        rv.setStyleSheet("font-size:10px; color:#94A3B8;")
        rv.setAlignment(Qt.AlignRight)
        right.addWidget(mv)
        right.addWidget(rv)
        outer.addLayout(right)

        return row
