STYLESHEET = """
/* ═══════════════════════════════════════════════
   FinanceApp Pro  ·  Light Theme
   ═══════════════════════════════════════════════ */

/* ── Base ── */
QMainWindow, QWidget {
    background-color : #F4F6FB;
    color            : #1A1F36;
    font-family      : 'Segoe UI', 'Arial', sans-serif;
    font-size        : 13px;
}

/* ── Scroll ── */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background   : transparent;
    width        : 5px;
    border-radius: 3px;
    margin       : 0;
}
QScrollBar::handle:vertical {
    background   : #C5D0E8;
    border-radius: 3px;
    min-height   : 24px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }

/* ── Barra de cotações ── */
#quoteBar {
    background-color: #FFFFFF;
    border-bottom   : 1px solid #E4EAF6;
}
#quoteChip {
    background   : #F0F5FF;
    border-radius: 8px;
    border       : 1px solid #DDE6FA;
    min-height   : 30px;
    max-height   : 30px;
}

/* ── Sidebar ── */
#sidebar {
    background-color: #FFFFFF;
    border-right    : 1px solid #E4EAF6;
}

/* ── Nav buttons ── */
#sidebar QPushButton {
    background   : transparent;
    color        : #64748B;
    border       : none;
    border-radius: 8px;
    text-align   : left;
    padding      : 10px 14px;
    font-size    : 13px;
    font-weight  : 500;
    min-height   : 42px;
}
#sidebar QPushButton:hover {
    background: #F4F6FB;
    color     : #1A1F36;
}
#sidebar QPushButton[active="true"] {
    background  : #EEF4FF;
    color       : #3D74E8;
    font-weight : 700;
    border-left : 3px solid #3D74E8;
    padding-left: 11px;
}

/* ── Cards ── */
QFrame[card="true"] {
    background   : #FFFFFF;
    border-radius: 14px;
    border       : 1px solid #E4EAF6;
}

/* ── Botões primários ── */
QPushButton {
    background-color: #3D74E8;
    color           : #FFFFFF;
    border          : none;
    border-radius   : 9px;
    padding         : 9px 20px;
    font-weight     : 600;
    font-size       : 13px;
    min-height      : 36px;
}
QPushButton:hover   { background-color: #2D62D4; }
QPushButton:pressed { background-color: #1E4DB0; }

QPushButton[role="danger"]        { background: #EF4444; }
QPushButton[role="danger"]:hover  { background: #DC2626; }
QPushButton[role="success"]       { background: #22C55E; }
QPushButton[role="success"]:hover { background: #16A34A; }
QPushButton[role="secondary"] {
    background: #F0F5FF;
    color     : #3D74E8;
    border    : 1.5px solid #C5D5F8;
}
QPushButton[role="secondary"]:hover { background: #E2ECFF; }

/* ── Inputs ── */
QLineEdit, QTextEdit, QComboBox,
QDateEdit, QSpinBox, QDoubleSpinBox {
    background   : #F7F9FF;
    border       : 1.5px solid #D1DAF0;
    border-radius: 9px;
    padding      : 8px 12px;
    color        : #1A1F36;
    font-size    : 13px;
    selection-background-color: #C5D5F8;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3D74E8;
    background  : #FFFFFF;
}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover,
QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #8AAAF0;
}

QComboBox { padding-right: 8px; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow {
    image       : none;
    border-left : 4px solid transparent;
    border-right: 4px solid transparent;
    border-top  : 5px solid #3D74E8;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background : #FFFFFF;
    border     : 1px solid #D1DAF0;
    border-radius: 9px;
    selection-background-color: #EEF4FF;
    selection-color: #1A1F36;
    padding    : 4px;
    outline    : 0;
}

/* ── Table ── */
QTableWidget {
    background    : transparent;
    border        : none;
    gridline-color: transparent;
    outline       : 0;
}
QTableWidget::item {
    padding      : 10px 8px;
    border-bottom: 1px solid #F0F4FF;
}
QTableWidget::item:selected {
    background: #EEF4FF;
    color     : #1A1F36;
}
QTableWidget::item:hover { background: #F7F9FF; }
QHeaderView::section {
    background   : #F7F9FF;
    color        : #94A3B8;
    padding      : 10px 8px;
    border       : none;
    border-bottom: 1.5px solid #E4EAF6;
    font-weight  : 700;
    font-size    : 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── Dialogs ── */
QDialog {
    background   : #FFFFFF;
    border-radius: 16px;
    border       : 1px solid #E4EAF6;
}

/* ── Tooltip ── */
QToolTip {
    background   : #1A1F36;
    color        : #FFFFFF;
    border       : none;
    border-radius: 7px;
    padding      : 6px 10px;
    font-size    : 12px;
}

/* ── CheckBox ── */
QCheckBox { color: #1A1F36; spacing: 8px; }
QCheckBox::indicator {
    width        : 17px;
    height       : 17px;
    border-radius: 5px;
    border       : 2px solid #C5D5F8;
    background   : #FFFFFF;
}
QCheckBox::indicator:checked {
    background  : #3D74E8;
    border-color: #3D74E8;
}

/* ── TabBar ── */
QTabWidget::pane  { border: none; background: transparent; }
QTabBar::tab {
    background   : transparent;
    color        : #94A3B8;
    padding      : 10px 22px;
    border-bottom: 2px solid transparent;
    font-size    : 13px;
    font-weight  : 500;
}
QTabBar::tab:selected {
    color        : #3D74E8;
    border-bottom: 2px solid #3D74E8;
}
QTabBar::tab:hover { color: #1A1F36; }

/* ── Calendar popup ── */
QCalendarWidget QWidget { background: #FFFFFF; color: #1A1F36; }
QCalendarWidget QAbstractItemView:enabled {
    background                : #FFFFFF;
    selection-background-color: #EEF4FF;
    selection-color           : #1A1F36;
}

/* ── SpinBox arrows ── */
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: transparent;
    border    : none;
    width     : 18px;
}
"""
