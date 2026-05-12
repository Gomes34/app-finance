from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
)
from PySide6.QtCore import Qt


class LoginDialog(QDialog):
    def __init__(self, expected_code: str, parent=None):
        super().__init__(parent)
        self._code     = expected_code
        self._attempts = 0
        self.setWindowTitle("FinanceApp Pro")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(48, 44, 48, 36)
        lay.setSpacing(0)

        logo = QLabel("FinanceApp Pro")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "font-size:24px; font-weight:800; color:#3D74E8;")
        lay.addWidget(logo)

        hint = QLabel("Insira seu código de acesso")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(
            "font-size:13px; color:#7A849E; margin-top:6px; margin-bottom:22px;")
        lay.addWidget(hint)

        self._inp = QLineEdit()
        self._inp.setEchoMode(QLineEdit.Password)
        self._inp.setPlaceholderText("Código de acesso")
        self._inp.setAlignment(Qt.AlignCenter)
        self._inp.setFixedHeight(48)
        self._inp.setStyleSheet(
            "font-size:16px; letter-spacing:3px;"
            "border-radius:12px; border:2px solid #CED8EE;"
            "background:#F7F9FF; padding:0 16px; color:#1A1F36;")
        self._inp.returnPressed.connect(self._confirm)
        lay.addWidget(self._inp)

        self._err = QLabel("")
        self._err.setAlignment(Qt.AlignCenter)
        self._err.setStyleSheet(
            "color:#EF4444; font-size:12px; min-height:20px;"
            "margin-top:6px;")
        lay.addWidget(self._err)

        lay.addStretch()

        btn = QPushButton("Entrar")
        btn.setFixedHeight(46)
        btn.setStyleSheet(
            "background:#3D74E8; color:#fff; border-radius:12px;"
            "font-size:14px; font-weight:700; border:none;")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._confirm)
        lay.addWidget(btn)

    def _confirm(self):
        entered = self._inp.text().strip()
        if entered == self._code:
            self.accept()
        else:
            self._attempts += 1
            self._inp.clear()
            self._inp.setStyleSheet(
                "font-size:16px; letter-spacing:3px;"
                "border-radius:12px; border:2px solid #EF4444;"
                "background:#FFF5F5; padding:0 16px; color:#1A1F36;")
            self._err.setText(
                f"Codigo incorreto  —  tentativa {self._attempts}")
