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
from ui.widgets       import NavButton, FadeStack, TickerBar
from ui.dashboard     import DashboardPage
from ui.transactions  import TransactionsPage
from ui.subscriptions import SubscriptionsPage
from ui.analytics     import AnalyticsPage
from ui.goals         import GoalsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("💰  FinanceApp Pro")
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

        # ticker de cotações
        self._ticker = TickerBar()
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

        logo = QLabel("  💎  FinanceApp")
        logo.setStyleSheet(
            "font-size:16px; font-weight:700; color:#3D74E8;"
            "padding:4px 4px 16px 4px;")
        sl.addWidget(logo)

        pages = [
            ("🏠", "Dashboard",   0),
            ("💳", "Transações",  1),
            ("🔄", "Assinaturas", 2),
            ("📊", "Analytics",   3),
            ("🎯", "Metas",       4),
        ]
        self._nav: list[NavButton] = []
        for icon, label, idx in pages:
            btn = NavButton(icon, label)
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

        self._dash  = DashboardPage()
        self._txs   = TransactionsPage()
        self._subs  = SubscriptionsPage()
        self._analy = AnalyticsPage()
        self._goals = GoalsPage()

        for page in (self._dash, self._txs,
                     self._subs, self._analy, self._goals):
            self._stack.addWidget(page)

        # cross-refresh: quando transação ou assinatura muda → atualiza dashboard
        self._txs.refresh_signal.connect(self._dash.refresh)
        self._subs.refresh_signal.connect(self._dash.refresh)

        body.addWidget(self._stack)
        self._go(0)

    def _go(self, idx: int):
        self._stack.go(idx)
        for i, btn in enumerate(self._nav):
            btn.set_active(i == idx)
        # analytics precisa de refresh explícito pois não tem showEvent
        if idx == 3:
            self._analy.refresh()

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

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()