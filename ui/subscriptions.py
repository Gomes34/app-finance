from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QDateEdit, QFrame, QScrollArea, QColorDialog,
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont
from datetime import datetime

import database as db
from ui.widgets import Card, KPICard, ConfirmDlg, clear_layout


# ── Card de assinatura ────────────────────────────────────────────────────────
class SubCard(Card):
    sig_edit   = Signal(int)
    sig_delete = Signal(int)
    sig_toggle = Signal(int)

    def __init__(self, sub, parent=None):
        super().__init__(parent)
        self.sub = sub
        self.setFixedHeight(110)
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 14, 0)
        lay.setSpacing(12)

        # faixa colorida
        stripe = QFrame()
        stripe.setFixedWidth(5)
        stripe.setStyleSheet(
            f"background:{self.sub['color']};"
            "border-top-left-radius:16px;"
            "border-bottom-left-radius:16px;")
        lay.addWidget(stripe)

        # ícone
        ic = QLabel(self.sub["category_icon"] or "🔄")
        ic.setFont(QFont("Segoe UI Emoji", 22))
        ic.setFixedWidth(36)
        lay.addWidget(ic)

        # info
        info = QVBoxLayout()
        info.setSpacing(3)
        nm = QLabel(self.sub["name"])
        nm.setStyleSheet(
            "font-size:14px; font-weight:700; color:#1A1F36;")
        ct = QLabel(self.sub["category_name"] or "—")
        ct.setStyleSheet("font-size:10px; color:#A0AABF;")
        dy = QLabel(f"📅  Vence dia {self.sub['billing_day']}")
        dy.setStyleSheet("font-size:10px; color:#7A849E;")
        info.addWidget(nm)
        info.addWidget(ct)
        info.addWidget(dy)
        lay.addLayout(info, 1)

        # valor
        ar = QVBoxLayout()
        ar.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        av = QLabel(f"R$ {self.sub['amount']:,.2f}")
        av.setStyleSheet(
            f"color:{self.sub['color']};"
            "font-size:17px; font-weight:700;")
        av.setAlignment(Qt.AlignRight)
        pm = QLabel("/ mês")
        pm.setStyleSheet("color:#A0AABF; font-size:10px;")
        pm.setAlignment(Qt.AlignRight)
        ar.addWidget(av)
        ar.addWidget(pm)
        lay.addLayout(ar)

        # ações
        ac = QVBoxLayout()
        ac.setSpacing(5)
        ac.setAlignment(Qt.AlignVCenter)

        ok = bool(self.sub["active"])
        tc = "#16A34A" if ok else "#9CA3AF"
        tb = QPushButton("✅ Ativa" if ok else "⏸ Pausada")
        tb.setFixedHeight(26)
        tb.setFixedWidth(90)
        tb.setStyleSheet(
            f"background:transparent; color:{tc};"
            f"border:1.5px solid {tc}; border-radius:7px;"
            "font-size:10px; font-weight:600; padding:0;")
        tb.setCursor(Qt.PointingHandCursor)
        tb.clicked.connect(lambda: self.sig_toggle.emit(self.sub["id"]))

        br2 = QHBoxLayout()
        br2.setSpacing(4)
        for emoji, sig in [("✏️", self.sig_edit), ("🗑️", self.sig_delete)]:
            b = QPushButton(emoji)
            b.setFixedSize(26, 26)
            b.setStyleSheet(
                "background:#F0F4FF; border-radius:6px;"
                "font-size:11px; padding:0; border:none;")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, s=sig: s.emit(self.sub["id"]))
            br2.addWidget(b)

        ac.addWidget(tb)
        ac.addLayout(br2)
        lay.addLayout(ac)


# ── Dialog ────────────────────────────────────────────────────────────────────
class SubDialog(QDialog):
    def __init__(self, parent=None, sub=None):
        super().__init__(parent)
        self._sub   = sub
        self._color = sub["color"] if sub else "#5B8DEF"
        self.setWindowTitle("Assinatura")
        self.setFixedSize(460, 480)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build()
        if sub:
            self._fill(sub)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 22)
        lay.setSpacing(12)

        t = QLabel("🔄  " +
                   ("Editar" if self._sub else "Nova") +
                   " Assinatura")
        t.setStyleSheet(
            "font-size:17px; font-weight:700; color:#1A1F36;")
        lay.addWidget(t)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Nome do serviço (ex: Netflix…)")
        self._name.setFixedHeight(42)
        lay.addWidget(self._name)

        r1 = QHBoxLayout()
        r1.setSpacing(10)
        self._amt = QDoubleSpinBox()
        self._amt.setRange(0.01, 9_999.99)
        self._amt.setDecimals(2)
        self._amt.setPrefix("R$ ")
        self._amt.setFixedHeight(42)

        self._day = QSpinBox()
        self._day.setRange(1, 31)
        self._day.setValue(1)
        self._day.setPrefix("Dia: ")
        self._day.setFixedHeight(42)
        self._day.setFixedWidth(110)

        r1.addWidget(self._amt)
        r1.addWidget(self._day)
        lay.addLayout(r1)

        self._cat = QComboBox()
        self._cat.setFixedHeight(42)
        for c in db.get_categories("expense"):
            self._cat.addItem(f"{c['icon']} {c['name']}", c["id"])
        lay.addWidget(self._cat)

        self._start = QDateEdit(QDate.currentDate())
        self._start.setCalendarPopup(True)
        self._start.setDisplayFormat("dd/MM/yyyy")
        self._start.setFixedHeight(42)
        lay.addWidget(self._start)

        # cor
        cr = QHBoxLayout()
        cl = QLabel("Cor:")
        cl.setStyleSheet("color:#7A849E; font-size:12px;")
        cl.setFixedWidth(36)
        self._cbtn = QPushButton()
        self._cbtn.setFixedSize(44, 36)
        self._cbtn.setCursor(Qt.PointingHandCursor)
        self._cbtn.setToolTip("Escolher cor")
        self._cbtn.clicked.connect(self._pick_color)
        self._update_cbtn()
        cr.addWidget(cl)
        cr.addWidget(self._cbtn)
        cr.addStretch()
        lay.addLayout(cr)

        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Observações…")
        self._notes.setMaximumHeight(68)
        lay.addWidget(self._notes)

        lay.addStretch()

        br = QHBoxLayout()
        br.setSpacing(10)
        bc = QPushButton("Cancelar")
        bc.setProperty("role", "secondary")
        bc.clicked.connect(self.reject)
        bs = QPushButton("✅  Salvar")
        bs.setProperty("role", "success")
        bs.clicked.connect(self._save)
        br.addWidget(bc)
        br.addWidget(bs)
        lay.addLayout(br)

    def _update_cbtn(self):
        self._cbtn.setStyleSheet(
            f"background:{self._color}; border-radius:8px; border:none;")

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self)
        if c.isValid():
            self._color = c.name()
            self._update_cbtn()

    def _fill(self, s):
        self._name.setText(s["name"])
        self._amt.setValue(float(s["amount"]))
        self._day.setValue(int(s["billing_day"]))
        if s["notes"]:
            self._notes.setText(s["notes"])
        for i in range(self._cat.count()):
            if self._cat.itemData(i) == s["category_id"]:
                self._cat.setCurrentIndex(i)
                break

    def _save(self):
        name = self._name.text().strip()
        if not name:
            self._name.setStyleSheet(
                "border:1.5px solid #EF4444; border-radius:10px;"
                "padding:8px 12px; background:#FFF5F5;")
            return
        amt    = self._amt.value()
        day    = self._day.value()
        cat_id = self._cat.currentData()
        start  = self._start.date().toString("yyyy-MM-dd")
        notes  = self._notes.toPlainText()

        if self._sub:
            db.update_subscription(
                self._sub["id"], name, amt, day, cat_id, notes, self._color)
        else:
            db.add_subscription(
                name, amt, day, cat_id, start, notes, self._color)
        self.accept()


# ── Página ────────────────────────────────────────────────────────────────────
class SubscriptionsPage(QWidget):
    refresh_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 20)
        lay.setSpacing(14)

        hdr = QHBoxLayout()
        t = QLabel("Assinaturas")
        t.setStyleSheet(
            "font-size:22px; font-weight:700; color:#1A1F36;")
        hdr.addWidget(t)
        hdr.addStretch()
        b = QPushButton("＋  Nova Assinatura")
        b.setFixedHeight(40)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(self._new)
        hdr.addWidget(b)
        lay.addLayout(hdr)

        self._kpi_row = QHBoxLayout()
        self._kpi_row.setSpacing(12)
        lay.addLayout(self._kpi_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._inner = QWidget()
        self._cards_lay = QVBoxLayout(self._inner)
        self._cards_lay.setSpacing(10)
        self._cards_lay.setContentsMargins(0, 0, 6, 0)
        scroll.setWidget(self._inner)
        lay.addWidget(scroll)

    def refresh(self):
        subs = db.get_subscriptions()

        # KPIs
        clear_layout(self._kpi_row)
        active   = [s for s in subs if s["active"]]
        inactive = [s for s in subs if not s["active"]]
        monthly  = sum(s["amount"] for s in active)

        for lbl, val, col, ic in [
            ("Mensal",   f"R$ {monthly:,.2f}",      "#EF4444", "💸"),
            ("Anual",    f"R$ {monthly * 12:,.2f}", "#3D74E8", "📅"),
            ("Ativas",   str(len(active)),           "#16A34A", "✅"),
            ("Pausadas", str(len(inactive)),         "#9CA3AF", "⏸"),
        ]:
            kpi = KPICard(lbl, val, "", ic, col)
            kpi.setFixedHeight(96)
            self._kpi_row.addWidget(kpi)

        # Cards
        clear_layout(self._cards_lay)

        if not subs:
            e = QLabel(
                "Nenhuma assinatura cadastrada.\n"
                "Clique em '＋ Nova Assinatura' para começar.")
            e.setAlignment(Qt.AlignCenter)
            e.setStyleSheet(
                "color:#A0AABF; font-size:14px; padding:40px;")
            self._cards_lay.addWidget(e)
        else:
            if active:
                lbl_a = QLabel("  ✅  Ativas")
                lbl_a.setStyleSheet(
                    "font-size:12px; color:#16A34A; font-weight:700;")
                self._cards_lay.addWidget(lbl_a)
                for s in active:
                    self._add_card(s)

            if inactive:
                lbl_i = QLabel("  ⏸  Pausadas")
                lbl_i.setStyleSheet(
                    "font-size:12px; color:#9CA3AF; font-weight:700;"
                    "margin-top:8px;")
                self._cards_lay.addWidget(lbl_i)
                for s in inactive:
                    self._add_card(s)

        self._cards_lay.addStretch()

    def _add_card(self, s):
        c = SubCard(s)
        c.sig_edit.connect(self._edit)
        c.sig_delete.connect(self._del)
        c.sig_toggle.connect(self._toggle)
        self._cards_lay.addWidget(c)

    def _new(self):
        dlg = SubDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()
            self.refresh_signal.emit()

    def _edit(self, sid: int):
        conn = db.get_connection()
        s = conn.execute("""
            SELECT s.*, c.name AS category_name, c.icon AS category_icon
            FROM subscriptions s
            LEFT JOIN categories c ON s.category_id = c.id
            WHERE s.id = ?
        """, (sid,)).fetchone()
        conn.close()
        if s:
            dlg = SubDialog(self, s)
            if dlg.exec() == QDialog.Accepted:
                self.refresh()
                self.refresh_signal.emit()

    def _toggle(self, sid: int):
        db.toggle_subscription(sid)
        self.refresh()
        self.refresh_signal.emit()

    def _del(self, sid: int):
        dlg = ConfirmDlg(
            "Excluir Assinatura",
            "Deseja excluir esta assinatura?",
            self)
        if dlg.exec() == QDialog.Accepted:
            db.delete_subscription(sid)
            self.refresh()
            self.refresh_signal.emit()