import os
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QFrame,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

import database as db
from services.quotes import fetch_quotes
from ui.theme         import STYLESHEET
from ui.widgets       import NavButton, FadeStack, QuoteBar
from ui.dashboard     import DashboardPage
from ui.transactions  import TransactionsPage
from ui.subscriptions import SubscriptionsPage
from ui.analytics     import AnalyticsPage
from ui.goals         import GoalsPage
from ui.invoice       import InvoicePage


def _read_access_code() -> str:
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ACCESS_CODE="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return ""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FinanceApp Pro")
        self.setMinimumSize(1080, 680)
        self.resize(1280, 800)
        self._build()
        self._load_quotes()

        self._qtimer = QTimer(self)
        self._qtimer.timeout.connect(self._load_quotes)
        self._qtimer.start(300_000)

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        vlay = QVBoxLayout(root)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        # barra de cotações fixa
        self._ticker = QuoteBar()
        vlay.addWidget(self._ticker)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        vlay.addLayout(body)

        # ── sidebar ──────────────────────────────────────────────────────────
        sb = QFrame()
        sb.setObjectName("sidebar")
        sb.setFixedWidth(210)
        sl = QVBoxLayout(sb)
        sl.setContentsMargins(10, 16, 10, 16)
        sl.setSpacing(3)

        logo = QLabel("FinanceApp")
        logo.setStyleSheet(
            "font-size:17px; font-weight:800; color:#3D74E8;"
            "padding:4px 4px 18px 8px; letter-spacing:0.5px;")
        sl.addWidget(logo)

        pages = [
            ("Dashboard",   0),
            ("Transacoes",  1),
            ("Assinaturas", 2),
            ("Analytics",   3),
            ("Metas",       4),
            ("Fatura",      5),
        ]
        self._nav: list[NavButton] = []
        for label, idx in pages:
            btn = NavButton(label)
            btn.clicked.connect(lambda _, i=idx: self._go(i))
            sl.addWidget(btn)
            self._nav.append(btn)

        sl.addStretch()

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            "background:#DDE4F0; margin:4px 0; max-height:1px;")
        sl.addWidget(sep)

        ver = QLabel(f"  v1.0  ·  {datetime.now().year}")
        ver.setStyleSheet(
            "color:#A0AABF; font-size:10px; padding:4px;")
        sl.addWidget(ver)
        body.addWidget(sb)

        # ── páginas ───────────────────────────────────────────────────────────
        self._stack = FadeStack()

        self._dash    = DashboardPage()
        self._txs     = TransactionsPage()
        self._subs    = SubscriptionsPage()
        self._analy   = AnalyticsPage()
        self._goals   = GoalsPage()
        self._invoice = InvoicePage()

        for page in (self._dash, self._txs,
                     self._subs, self._analy, self._goals, self._invoice):
            self._stack.addWidget(page)

        self._txs.refresh_signal.connect(self._dash.refresh)
        self._txs.refresh_signal.connect(self._invoice.refresh)
        self._subs.refresh_signal.connect(self._dash.refresh)

        body.addWidget(self._stack)
        self._go(0)

    def _go(self, idx: int):
        self._stack.go(idx)
        for i, btn in enumerate(self._nav):
            btn.set_active(i == idx)
        if idx == 3:
            self._analy.refresh()
        if idx == 5:
            self._invoice.refresh()

    def _load_quotes(self):
        fetch_quotes(callback=self._on_quotes)

    def _on_quotes(self, quotes: dict, last_update: str):
        self._ticker.update_quotes(quotes, last_update)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Segoe UI", 10))

    db.init_db()

    code = _read_access_code()
    if code:
        from ui.login import LoginDialog
        dlg = LoginDialog(code)
        if dlg.exec() != LoginDialog.Accepted:
            sys.exit(0)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
