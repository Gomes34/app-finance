from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QLineEdit, QDoubleSpinBox, QDateEdit,
    QFrame, QScrollArea, QColorDialog, QGridLayout,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from datetime import datetime

import database as db
from ui.widgets import Card, KPICard, SmoothBar, ConfirmDlg, clear_layout


# ── Card de meta ──────────────────────────────────────────────────────────────
class GoalCard(Card):
    def __init__(self, goal, on_edit, on_del, on_dep, parent=None):
        super().__init__(parent)
        self.goal = goal
        self.setFixedHeight(160)
        self._on_edit = on_edit
        self._on_del  = on_del
        self._on_dep  = on_dep
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(6)

        curr   = float(self.goal["current_amount"])
        target = float(self.goal["target_amount"])
        pct    = min((curr / target * 100) if target > 0 else 0, 100)
        done   = pct >= 100

        # cabeçalho
        hdr = QHBoxLayout()
        ic = QLabel(self.goal["icon"] or "🎯")
        ic.setFont(QFont("Segoe UI Emoji", 20))
        ic.setFixedWidth(32)
        nm = QLabel(self.goal["name"])
        nm.setStyleSheet(
            "font-size:14px; font-weight:700; color:#1A1F36;")
        hdr.addWidget(ic)
        hdr.addWidget(nm)
        hdr.addStretch()

        for emoji, cb in [
            ("✏️", lambda: self._on_edit(self.goal["id"])),
            ("🗑️", lambda: self._on_del(self.goal["id"])),
        ]:
            b = QPushButton(emoji)
            b.setFixedSize(26, 26)
            b.setStyleSheet(
                "background:#F0F4FF; border-radius:6px;"
                "font-size:11px; padding:0; border:none;")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(cb)
            hdr.addWidget(b)
        lay.addLayout(hdr)

        # progresso
        pr = QHBoxLayout()
        cl = QLabel(f"R$ {curr:,.2f}")
        cl.setStyleSheet(
            f"color:{self.goal['color']};"
            "font-size:14px; font-weight:700;")
        tl = QLabel(f"  /  R$ {target:,.2f}")
        tl.setStyleSheet("color:#A0AABF; font-size:11px;")
        pl = QLabel("✅ Concluída!" if done else f"{pct:.0f}%")
        pl.setStyleSheet(
            f"color:{'#16A34A' if done else self.goal['color']};"
            "font-weight:700; font-size:12px;")
        pr.addWidget(cl)
        pr.addWidget(tl)
        pr.addStretch()
        pr.addWidget(pl)
        lay.addLayout(pr)

        bar = SmoothBar(pct, 100, self.goal["color"])
        lay.addWidget(bar)

        # rodapé
        ft = QHBoxLayout()
        if self.goal["deadline"]:
            try:
                dl   = datetime.strptime(
                    self.goal["deadline"], "%Y-%m-%d")
                days = (dl - datetime.now()).days
                dtxt = f"📅  {self.goal['deadline']}  ({days}d)"
                dcol = "#EF4444" if days < 30 else "#7A849E"
            except Exception:
                dtxt = str(self.goal["deadline"])
                dcol = "#7A849E"
            dl_lbl = QLabel(dtxt)
            dl_lbl.setStyleSheet(
                f"font-size:10px; color:{dcol};")
            ft.addWidget(dl_lbl)
        ft.addStretch()

        dep = QPushButton("💰  Depositar")
        dep.setFixedHeight(26)
        c = self.goal["color"]
        dep.setStyleSheet(
            f"background:{c}22; color:{c}; border:1.5px solid {c};"
            "border-radius:7px; font-size:10px; font-weight:700;"
            "padding:0 8px;")
        dep.setCursor(Qt.PointingHandCursor)
        dep.clicked.connect(lambda: self._on_dep(self.goal["id"]))
        ft.addWidget(dep)
        lay.addLayout(ft)


# ── Diálogos ──────────────────────────────────────────────────────────────────
class GoalDialog(QDialog):
    def __init__(self, parent=None, goal=None):
        super().__init__(parent)
        self._goal  = goal
        self._color = goal["color"] if goal else "#5B8DEF"
        self.setWindowTitle("Meta")
        self.setFixedSize(420, 400)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build()
        if goal:
            self._fill(goal)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 22)
        lay.setSpacing(12)

        t = QLabel("🎯  " +
                   ("Editar" if self._goal else "Nova") + " Meta")
        t.setStyleSheet(
            "font-size:17px; font-weight:700; color:#1A1F36;")
        lay.addWidget(t)

        # ícone + nome
        r = QHBoxLayout()
        r.setSpacing(10)
        self._icon = QLineEdit("🎯")
        self._icon.setFixedSize(54, 42)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setStyleSheet("font-size:22px;")
        self._name = QLineEdit()
        self._name.setPlaceholderText("Nome da meta…")
        self._name.setFixedHeight(42)
        r.addWidget(self._icon)
        r.addWidget(self._name)
        lay.addLayout(r)

        self._target = QDoubleSpinBox()
        self._target.setRange(1.00, 99_999_999.00)
        self._target.setDecimals(2)
        self._target.setPrefix("R$ ")
        self._target.setFixedHeight(42)
        lay.addWidget(self._target)

        self._dl = QDateEdit(QDate.currentDate().addMonths(6))
        self._dl.setCalendarPopup(True)
        self._dl.setDisplayFormat("dd/MM/yyyy")
        self._dl.setFixedHeight(42)
        lay.addWidget(self._dl)

        # cor
        cr = QHBoxLayout()
        cl = QLabel("Cor:")
        cl.setStyleSheet("color:#7A849E; font-size:12px;")
        cl.setFixedWidth(36)
        self._cbtn = QPushButton()
        self._cbtn.setFixedSize(44, 36)
        self._cbtn.setCursor(Qt.PointingHandCursor)
        self._cbtn.clicked.connect(self._pick)
        self._upd_cbtn()
        cr.addWidget(cl)
        cr.addWidget(self._cbtn)
        cr.addStretch()
        lay.addLayout(cr)

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

    def _upd_cbtn(self):
        self._cbtn.setStyleSheet(
            f"background:{self._color}; border-radius:8px; border:none;")

    def _pick(self):
        c = QColorDialog.getColor(QColor(self._color), self)
        if c.isValid():
            self._color = c.name()
            self._upd_cbtn()

    def _fill(self, g):
        self._icon.setText(g["icon"] or "🎯")
        self._name.setText(g["name"])
        self._target.setValue(float(g["target_amount"]))
        if g["deadline"]:
            d = QDate.fromString(g["deadline"], "yyyy-MM-dd")
            if d.isValid():
                self._dl.setDate(d)

    def _save(self):
        name = self._name.text().strip()
        if not name:
            self._name.setStyleSheet(
                "border:1.5px solid #EF4444; border-radius:10px;"
                "padding:8px 12px; background:#FFF5F5;")
            return
        icon   = self._icon.text().strip() or "🎯"
        target = self._target.value()
        dl     = self._dl.date().toString("yyyy-MM-dd")

        if self._goal:
            conn = db.get_connection()
            conn.execute(
                "UPDATE goals SET name=?, target_amount=?, deadline=?,"
                " color=?, icon=? WHERE id=?",
                (name, target, dl, self._color, icon, self._goal["id"]))
            conn.commit()
            conn.close()
        else:
            db.add_goal(name, target, dl, self._color, icon)
        self.accept()


class DepositDialog(QDialog):
    def __init__(self, goal, parent=None):
        super().__init__(parent)
        self._goal = goal
        self.setWindowTitle("Depositar")
        self.setFixedSize(360, 215)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(12)

        t = QLabel(f"💰  Depositar em {self._goal['name']}")
        t.setStyleSheet(
            "font-size:15px; font-weight:700; color:#1A1F36;")
        t.setWordWrap(True)
        lay.addWidget(t)

        curr   = float(self._goal["current_amount"])
        target = float(self._goal["target_amount"])
        info   = QLabel(
            f"Atual: R$ {curr:,.2f}   →   Meta: R$ {target:,.2f}")
        info.setStyleSheet("color:#7A849E; font-size:11px;")
        lay.addWidget(info)

        self._amt = QDoubleSpinBox()
        self._amt.setRange(0.01, 999_999.99)
        self._amt.setDecimals(2)
        self._amt.setPrefix("R$ ")
        self._amt.setFixedHeight(42)
        lay.addWidget(self._amt)

        lay.addStretch()

        br = QHBoxLayout()
        br.setSpacing(10)
        bc = QPushButton("Cancelar")
        bc.setProperty("role", "secondary")
        bc.clicked.connect(self.reject)
        bs = QPushButton("✅  Depositar")
        bs.setProperty("role", "success")
        bs.clicked.connect(self._deposit)
        br.addWidget(bc)
        br.addWidget(bs)
        lay.addLayout(br)

    def _deposit(self):
        new_val = float(self._goal["current_amount"]) + self._amt.value()
        db.update_goal_amount(self._goal["id"], new_val)
        self.accept()


# ── Página ────────────────────────────────────────────────────────────────────
class GoalsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 20)
        lay.setSpacing(14)

        hdr = QHBoxLayout()
        t = QLabel("Metas Financeiras")
        t.setStyleSheet(
            "font-size:22px; font-weight:700; color:#1A1F36;")
        hdr.addWidget(t)
        hdr.addStretch()
        b = QPushButton("＋  Nova Meta")
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
        self._grid  = QGridLayout(self._inner)
        self._grid.setSpacing(14)
        self._grid.setContentsMargins(0, 0, 6, 0)
        scroll.setWidget(self._inner)
        lay.addWidget(scroll)

    def refresh(self):
        goals = db.get_goals()

        # KPIs
        clear_layout(self._kpi_row)
        total_t = sum(float(g["target_amount"])  for g in goals)
        total_c = sum(float(g["current_amount"]) for g in goals)
        done    = sum(
            1 for g in goals
            if float(g["current_amount"]) >= float(g["target_amount"]))

        for lbl, val, col, ic in [
            ("Total Metas",  f"R$ {total_t:,.2f}", "#5B8DEF", "🎯"),
            ("Guardado",     f"R$ {total_c:,.2f}", "#16A34A", "💰"),
            ("Concluídas",   str(done),             "#F59E0B", "✅"),
            ("Em andamento", str(len(goals) - done),"#EF4444", "⏳"),
        ]:
            kpi = KPICard(lbl, val, "", ic, col)
            kpi.setFixedHeight(96)
            self._kpi_row.addWidget(kpi)

        # Grid de cards
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not goals:
            e = QLabel(
                "Nenhuma meta cadastrada.\n"
                "Defina seus objetivos financeiros!")
            e.setAlignment(Qt.AlignCenter)
            e.setStyleSheet(
                "color:#A0AABF; font-size:14px; padding:40px;")
            self._grid.addWidget(e, 0, 0, 1, 2)
        else:
            for i, g in enumerate(goals):
                card = GoalCard(
                    g,
                    on_edit=self._edit,
                    on_del=self._del,
                    on_dep=self._deposit,
                )
                self._grid.addWidget(card, i // 2, i % 2)

    def _new(self):
        dlg = GoalDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    def _edit(self, gid: int):
        conn = db.get_connection()
        g = conn.execute(
            "SELECT * FROM goals WHERE id=?", (gid,)).fetchone()
        conn.close()
        if g:
            dlg = GoalDialog(self, g)
            if dlg.exec() == QDialog.Accepted:
                self.refresh()

    def _del(self, gid: int):
        dlg = ConfirmDlg(
            "Excluir Meta",
            "Deseja excluir esta meta?",
            self)
        if dlg.exec() == QDialog.Accepted:
            db.delete_goal(gid)
            self.refresh()

    def _deposit(self, gid: int):
        conn = db.get_connection()
        g = conn.execute(
            "SELECT * FROM goals WHERE id=?", (gid,)).fetchone()
        conn.close()
        if g:
            dlg = DepositDialog(g, self)
            if dlg.exec() == QDialog.Accepted:
                self.refresh()