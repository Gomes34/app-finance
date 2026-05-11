from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit, QComboBox,
    QTextEdit, QDateEdit, QDoubleSpinBox, QFrame, QHeaderView,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont
from datetime import datetime

import database as db
from ui.widgets import Card, ConfirmDlg, clear_layout


# ══════════════════════════════════════════════════════════════════════════════
#  Dialog de criação / edição
# ══════════════════════════════════════════════════════════════════════════════
class TxDialog(QDialog):
    def __init__(self, parent=None, tx=None):
        super().__init__(parent)
        self._tx   = tx
        self._type = "expense"
        self.setWindowTitle("Transação")
        self.setFixedSize(480, 530)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build()
        if tx:
            self._fill(tx)
        else:
            self._apply_style()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 22)
        lay.setSpacing(12)

        title = QLabel(
            "💸  " + ("Editar" if self._tx else "Nova") + " Transação")
        title.setStyleSheet(
            "font-size:17px; font-weight:700; color:#1A1F36;")
        lay.addWidget(title)

        # tipo
        tr = QHBoxLayout()
        tr.setSpacing(8)
        self._btn_exp = QPushButton("💸  Despesa")
        self._btn_inc = QPushButton("💰  Receita")
        for b in (self._btn_exp, self._btn_inc):
            b.setFixedHeight(40)
            b.setCursor(Qt.PointingHandCursor)
        tr.addWidget(self._btn_exp)
        tr.addWidget(self._btn_inc)
        lay.addLayout(tr)

        # descrição
        self._desc = QLineEdit()
        self._desc.setPlaceholderText("Descrição…")
        self._desc.setFixedHeight(42)
        lay.addWidget(self._desc)

        # valor
        ar = QHBoxLayout()
        ar.setSpacing(8)
        rl = QLabel("R$")
        rl.setStyleSheet(
            "font-size:15px; font-weight:700; color:#3D74E8;")
        rl.setFixedWidth(30)
        self._amt = QDoubleSpinBox()
        self._amt.setRange(0.01, 9_999_999.99)
        self._amt.setDecimals(2)
        self._amt.setValue(0.01)
        self._amt.setFixedHeight(42)
        ar.addWidget(rl)
        ar.addWidget(self._amt)
        lay.addLayout(ar)

        # categoria — criado ANTES de conectar os botões de tipo
        self._cat = QComboBox()
        self._cat.setFixedHeight(42)
        lay.addWidget(self._cat)

        # data
        self._date = QDateEdit(QDate.currentDate())
        self._date.setCalendarPopup(True)
        self._date.setDisplayFormat("dd/MM/yyyy")
        self._date.setFixedHeight(42)
        lay.addWidget(self._date)

        # notas
        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Observações (opcional)…")
        self._notes.setMaximumHeight(72)
        lay.addWidget(self._notes)

        lay.addStretch()

        # botões
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

        # conecta APÓS _cat estar criado
        self._btn_exp.clicked.connect(lambda: self._set_type("expense"))
        self._btn_inc.clicked.connect(lambda: self._set_type("income"))

        # carrega categorias padrão
        self._reload_cats("expense")

    def _set_type(self, t: str):
        self._type = t
        self._reload_cats(t)
        self._apply_style()

    def _reload_cats(self, t: str):
        self._cat.blockSignals(True)
        self._cat.clear()
        for c in db.get_categories(t):
            self._cat.addItem(f"{c['icon']} {c['name']}", c["id"])
        self._cat.blockSignals(False)

    def _apply_style(self):
        on  = "border-radius:10px;font-weight:700;font-size:13px;padding:8px 16px;border:none;"
        off = "background:#F0F4FF;color:#7A849E;border-radius:10px;font-size:13px;padding:8px 16px;border:none;"
        if self._type == "expense":
            self._btn_exp.setStyleSheet(f"background:#EF4444;color:#fff;{on}")
            self._btn_inc.setStyleSheet(off)
        else:
            self._btn_inc.setStyleSheet(f"background:#22C55E;color:#fff;{on}")
            self._btn_exp.setStyleSheet(off)

    def _fill(self, tx):
        self._type = tx["type"]
        self._reload_cats(self._type)
        self._apply_style()
        self._desc.setText(tx["description"])
        self._amt.setValue(float(tx["amount"]))
        d = QDate.fromString(tx["date"], "yyyy-MM-dd")
        if d.isValid():
            self._date.setDate(d)
        if tx["notes"]:
            self._notes.setText(tx["notes"])
        for i in range(self._cat.count()):
            if self._cat.itemData(i) == tx["category_id"]:
                self._cat.setCurrentIndex(i)
                break

    def _save(self):
        desc = self._desc.text().strip()
        if not desc:
            self._desc.setStyleSheet(
                "border:1.5px solid #EF4444;border-radius:10px;"
                "padding:8px 12px;background:#FFF5F5;")
            self._desc.setPlaceholderText("⚠ Informe uma descrição")
            return
        amt    = self._amt.value()
        cat_id = self._cat.currentData()
        date   = self._date.date().toString("yyyy-MM-dd")
        notes  = self._notes.toPlainText()
        if self._tx:
            db.update_transaction(
                self._tx["id"], desc, amt,
                self._type, cat_id, date, notes)
        else:
            db.add_transaction(
                desc, amt, self._type, cat_id, date, notes)
        self.accept()

    # data salva é acessível após accept()
    def saved_date(self) -> QDate:
        return self._date.date()


# ══════════════════════════════════════════════════════════════════════════════
#  Página de Transações
# ══════════════════════════════════════════════════════════════════════════════
class TransactionsPage(QWidget):
    refresh_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    # ── build ─────────────────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 20)
        lay.setSpacing(14)

        # cabeçalho
        hdr = QHBoxLayout()
        t = QLabel("Transações")
        t.setStyleSheet("font-size:22px;font-weight:700;color:#1A1F36;")
        hdr.addWidget(t)
        hdr.addStretch()
        btn_new = QPushButton("＋  Nova Transação")
        btn_new.setFixedHeight(40)
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.clicked.connect(self._new)
        hdr.addWidget(btn_new)
        lay.addLayout(hdr)

        # filtros
        fc = Card()
        fl = QHBoxLayout(fc)
        fl.setContentsMargins(14, 10, 14, 10)
        fl.setSpacing(10)

        self._mcb = QComboBox()
        self._mcb.setFixedHeight(36)
        _months = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                   "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        for i, mn in enumerate(_months):
            self._mcb.addItem(mn, i + 1)

        self._ycb = QComboBox()
        self._ycb.setFixedHeight(36)

        self._tcb = QComboBox()
        self._tcb.addItems(["Todos","Receitas","Despesas"])
        self._tcb.setFixedHeight(36)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Buscar descrição…")
        self._search.setFixedHeight(36)

        for w in (self._mcb, self._ycb, self._tcb):
            fl.addWidget(w)
        fl.addWidget(self._search, 1)
        lay.addWidget(fc)

        # conecta sinais APÓS criação
        self._mcb.currentIndexChanged.connect(self._on_filter)
        self._ycb.currentIndexChanged.connect(self._on_filter)
        self._tcb.currentIndexChanged.connect(self._on_filter)
        self._search.textChanged.connect(self._on_filter)

        # mini-cards resumo
        self._sum_row = QHBoxLayout()
        self._sum_row.setSpacing(10)
        lay.addLayout(self._sum_row)

        # tabela
        tc = Card()
        tl = QVBoxLayout(tc)
        tl.setContentsMargins(0, 0, 0, 0)

        self._tbl = QTableWidget()
        self._tbl.setColumnCount(7)
        self._tbl.setHorizontalHeaderLabels(
            ["", "Descrição", "Categoria", "Tipo", "Valor", "Data", ""])
        self._tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch)
        for col, w in [(0,40),(2,130),(3,90),(4,140),(5,104),(6,84)]:
            self._tbl.setColumnWidth(col, w)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setShowGrid(False)
        self._tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self._tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.setStyleSheet(
            "QTableWidget{alternate-background-color:#F7F9FF;background:transparent;}")
        tl.addWidget(self._tbl)
        lay.addWidget(tc)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _populate_years(self):
        """Popula combo de anos com base nos dados + ano atual."""
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT DISTINCT strftime('%Y',date) AS y "
            "FROM transactions ORDER BY y DESC"
        ).fetchall()
        conn.close()

        years = sorted({int(r["y"]) for r in rows if r["y"]},
                       reverse=True)
        now_y = datetime.now().year
        if now_y not in years:
            years.insert(0, now_y)

        self._ycb.blockSignals(True)
        self._ycb.clear()
        for y in years:
            self._ycb.addItem(str(y), y)
        self._ycb.blockSignals(False)

    def _set_filter_to(self, month: int, year: int):
        """Posiciona combos no mês/ano informado sem disparar refresh duplo."""
        self._mcb.blockSignals(True)
        self._ycb.blockSignals(True)

        self._mcb.setCurrentIndex(month - 1)

        idx_y = next(
            (i for i in range(self._ycb.count())
             if self._ycb.itemData(i) == year), 0)
        self._ycb.setCurrentIndex(idx_y)

        self._mcb.blockSignals(False)
        self._ycb.blockSignals(False)

    def _best_period(self) -> tuple[int, int]:
        """
        Retorna (month, year) da transação mais recente no banco.
        Se não houver transações, retorna o mês/ano atual.
        """
        conn = db.get_connection()
        row = conn.execute(
            "SELECT date FROM transactions ORDER BY date DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if row:
            try:
                d = datetime.strptime(row["date"], "%Y-%m-%d")
                return d.month, d.year
            except Exception:
                pass
        now = datetime.now()
        return now.month, now.year

    def _on_filter(self):
        """Chamado quando qualquer filtro muda."""
        self.refresh()

    # ── showEvent ─────────────────────────────────────────────────────────────
    def showEvent(self, event):
        """Reinicializa ao exibir a página."""
        super().showEvent(event)
        self._populate_years()
        m, y = self._best_period()
        self._set_filter_to(m, y)
        self.refresh()

    # ── refresh ───────────────────────────────────────────────────────────────
    def refresh(self):
        month = self._mcb.currentData()
        year  = self._ycb.currentData()
        if month is None or year is None:
            return

        txs  = db.get_transactions(month, year)
        tf   = self._tcb.currentIndex()
        srch = self._search.text().lower().strip()

        filtered = [
            t for t in txs
            if (tf == 0
                or (tf == 1 and t["type"] == "income")
                or (tf == 2 and t["type"] == "expense"))
            and (not srch or srch in t["description"].lower())
        ]

        # ── resumo ──
        clear_layout(self._sum_row)
        income  = sum(t["amount"] for t in filtered if t["type"] == "income")
        expense = sum(t["amount"] for t in filtered if t["type"] == "expense")
        bal     = income - expense
        for lbl, val, col in [
            ("Receitas", f"R$ {income:,.2f}",  "#16A34A"),
            ("Despesas", f"R$ {expense:,.2f}", "#DC2626"),
            ("Saldo",    f"R$ {bal:,.2f}",
             "#3D74E8" if bal >= 0 else "#DC2626"),
        ]:
            mini = Card()
            mini.setFixedHeight(62)
            ml = QHBoxLayout(mini)
            ml.setContentsMargins(16, 0, 16, 0)
            vl = QVBoxLayout()
            vl.setSpacing(1)
            l1 = QLabel(lbl)
            l1.setStyleSheet("color:#7A849E;font-size:11px;font-weight:600;")
            l2 = QLabel(val)
            l2.setStyleSheet(f"color:{col};font-size:15px;font-weight:700;")
            vl.addWidget(l1)
            vl.addWidget(l2)
            ml.addLayout(vl)
            self._sum_row.addWidget(mini)

        # ── tabela ──
        # limpa spans anteriores e reseta
        self._tbl.clearSpans()
        self._tbl.setSortingEnabled(False)

        if not filtered:
            # mensagem de vazio como widget overlay, NÃO como célula com span
            self._tbl.setRowCount(0)
            self._show_empty(
                f"Nenhuma transação em "
                f"{self._mcb.currentText()} / {year}")
            return

        self._hide_empty()
        self._tbl.setRowCount(len(filtered))

        for i, t in enumerate(filtered):
            self._tbl.setRowHeight(i, 48)
            self._fill_row(i, t)

        self._tbl.setSortingEnabled(True)

    def _fill_row(self, i: int, t):
        """Preenche uma linha da tabela com dados da transação."""

        # col 0 — ícone
        ic = QTableWidgetItem(t["category_icon"] or "💰")
        ic.setTextAlignment(Qt.AlignCenter)
        ic.setFont(QFont("Segoe UI Emoji", 16))
        ic.setFlags(ic.flags() & ~Qt.ItemIsEditable)
        self._tbl.setItem(i, 0, ic)

        # col 1 — descrição
        desc = QTableWidgetItem(t["description"])
        desc.setFont(QFont("Segoe UI", 12, QFont.Bold))
        desc.setFlags(desc.flags() & ~Qt.ItemIsEditable)
        self._tbl.setItem(i, 1, desc)

        # col 2 — categoria
        cat = QTableWidgetItem(t["category_name"] or "—")
        cat.setForeground(QColor(t["category_color"] or "#7A849E"))
        cat.setFlags(cat.flags() & ~Qt.ItemIsEditable)
        self._tbl.setItem(i, 2, cat)

        # col 3 — tipo
        is_inc = t["type"] == "income"
        tc_col = "#16A34A" if is_inc else "#DC2626"
        tp = QTableWidgetItem("📈 Receita" if is_inc else "📉 Despesa")
        tp.setForeground(QColor(tc_col))
        tp.setTextAlignment(Qt.AlignCenter)
        tp.setFlags(tp.flags() & ~Qt.ItemIsEditable)
        self._tbl.setItem(i, 3, tp)

        # col 4 — valor
        sign = "+" if is_inc else "−"
        av = QTableWidgetItem(f"{sign} R$ {float(t['amount']):,.2f}")
        av.setForeground(QColor(tc_col))
        av.setFont(QFont("Segoe UI", 12, QFont.Bold))
        av.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        av.setFlags(av.flags() & ~Qt.ItemIsEditable)
        self._tbl.setItem(i, 4, av)

        # col 5 — data
        dv = QTableWidgetItem(t["date"])
        dv.setForeground(QColor("#A0AABF"))
        dv.setTextAlignment(Qt.AlignCenter)
        dv.setFlags(dv.flags() & ~Qt.ItemIsEditable)
        self._tbl.setItem(i, 5, dv)

        # col 6 — ações (widget)
        act_w = QWidget()
        act_l = QHBoxLayout(act_w)
        act_l.setContentsMargins(4, 4, 4, 4)
        act_l.setSpacing(4)
        for emoji, cb in [
            ("✏️", lambda _, tid=t["id"]: self._edit(tid)),
            ("🗑️", lambda _, tid=t["id"]: self._delete(tid)),
        ]:
            b = QPushButton(emoji)
            b.setFixedSize(32, 32)
            b.setStyleSheet(
                "background:#F0F4FF;border-radius:8px;"
                "font-size:14px;padding:0;border:none;")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(cb)
            act_l.addWidget(b)
        self._tbl.setCellWidget(i, 6, act_w)

    # ── overlay de "vazio" ────────────────────────────────────────────────────
    def _show_empty(self, msg: str):
        if not hasattr(self, "_empty_lbl"):
            self._empty_lbl = QLabel(parent=self._tbl.viewport())
            self._empty_lbl.setAlignment(Qt.AlignCenter)
            self._empty_lbl.setStyleSheet(
                "color:#A0AABF;font-size:14px;background:transparent;")
        self._empty_lbl.setText(msg)
        self._empty_lbl.resize(self._tbl.viewport().size())
        self._empty_lbl.show()

    def _hide_empty(self):
        if hasattr(self, "_empty_lbl"):
            self._empty_lbl.hide()

    # ── actions ───────────────────────────────────────────────────────────────
    def _new(self):
        dlg = TxDialog(self)
        if dlg.exec() == QDialog.Accepted:
            # vai para o período da transação salva
            d = dlg.saved_date()
            self._populate_years()
            self._set_filter_to(d.month(), d.year())
            self.refresh()
            self.refresh_signal.emit()

    def _edit(self, tid: int):
        conn = db.get_connection()
        t = conn.execute("""
            SELECT t.*,
                   c.name  AS category_name,
                   c.color AS category_color,
                   c.icon  AS category_icon
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.id = ?
        """, (tid,)).fetchone()
        conn.close()
        if not t:
            return

        dlg = TxDialog(self, t)
        if dlg.exec() == QDialog.Accepted:
            # vai para o período da data editada
            d = dlg.saved_date()
            self._populate_years()
            self._set_filter_to(d.month(), d.year())
            self.refresh()
            self.refresh_signal.emit()

    def _delete(self, tid: int):
        dlg = ConfirmDlg(
            "Excluir Transação",
            "Confirma a exclusão desta transação?\n"
            "Esta ação não pode ser desfeita.",
            self,
        )
        if dlg.exec() == QDialog.Accepted:
            db.delete_transaction(tid)
            self.refresh()
            self.refresh_signal.emit()

    def resizeEvent(self, event):
        """Redimensiona o overlay de vazio quando a janela muda."""
        super().resizeEvent(event)
        if hasattr(self, "_empty_lbl") and self._empty_lbl.isVisible():
            self._empty_lbl.resize(self._tbl.viewport().size())