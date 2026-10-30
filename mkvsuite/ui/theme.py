"""Look and feel: light/dark palettes, one stylesheet, bigger controls (the Chromebook screen is dense)."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle

LIGHT = dict(bg="#f4f5f7", surface="#ffffff", alt="#f8f9fb", border="#dcdfe5", border_strong="#b8bdc7",
             text="#1f2937", muted="#6b7280", accent="#2563eb", accent_hover="#1d4ed8", accent_off="#a5b4d6",
             hover="#eef1f6", selection="#dbe7ff", header="#f1f3f7", handle="#c4c9d2", warn_bg="#fef3c7",
             warn_border="#f59e0b", warn_text="#78350f", danger="#dc2626")
DARK = dict(bg="#111827", surface="#1b2433", alt="#202b3d", border="#334155", border_strong="#475569",
            text="#e5e7eb", muted="#9ca3af", accent="#3b82f6", accent_hover="#2563eb", accent_off="#3b4a66",
            hover="#263349", selection="#1e3a6e", header="#1f2a3c", handle="#475569", warn_bg="#3b2f12",
            warn_border="#b45309", warn_text="#fde68a", danger="#f87171")

_style_ref = None


class AppStyle(QProxyStyle):
    """Fusion with larger check boxes / radio buttons (easier to hit on a touchpad or touchscreen)."""
    def __init__(self):
        super().__init__("Fusion")

    def pixelMetric(self, metric, option=None, widget=None):
        if metric in (QStyle.PM_IndicatorWidth, QStyle.PM_IndicatorHeight,
                      QStyle.PM_ExclusiveIndicatorWidth, QStyle.PM_ExclusiveIndicatorHeight):
            return 20
        if metric == QStyle.PM_ScrollBarExtent:
            return 12
        return super().pixelMetric(metric, option, widget)


def resolve(mode):
    if mode in ("light", "dark"):
        return mode
    try:
        return "dark" if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark else "light"
    except AttributeError:
        return "light"


def _palette(c):
    p = QPalette()
    q = QColor
    for role, key in ((QPalette.Window, "bg"), (QPalette.Base, "surface"), (QPalette.AlternateBase, "alt"),
                      (QPalette.Button, "surface"), (QPalette.Text, "text"), (QPalette.WindowText, "text"),
                      (QPalette.ButtonText, "text"), (QPalette.ToolTipBase, "surface"), (QPalette.ToolTipText, "text"),
                      (QPalette.Highlight, "accent"), (QPalette.PlaceholderText, "muted"), (QPalette.Link, "accent"),
                      (QPalette.Mid, "border"), (QPalette.Midlight, "hover"), (QPalette.Dark, "border_strong")):
        p.setColor(role, q(c[key]))
    p.setColor(QPalette.HighlightedText, q("#ffffff"))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, role, q(c["muted"]))
    return p


def stylesheet(c):
    return f"""
QWidget {{ color: {c['text']}; }}
QLabel {{ background: transparent; }}
QLabel#pageTitle {{ font-size: 21pt; font-weight: 700; }}
QLabel#muted {{ color: {c['muted']}; }}
QLabel#sectionTitle {{ font-weight: 700; font-size: 12pt; }}
QLabel#appName {{ font-size: 14pt; font-weight: 700; }}

QFrame#sidebar {{ background: {c['surface']}; border: none; border-right: 1px solid {c['border']}; }}
QListWidget#nav {{ background: transparent; border: none; outline: 0; font-size: 12pt; }}
QListWidget#nav::item {{ padding: 13px 14px; margin: 2px 0; border-radius: 9px; }}
QListWidget#nav::item:hover {{ background: {c['hover']}; }}
QListWidget#nav::item:selected {{ background: {c['accent']}; color: white; }}

QFrame#card {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 12px; }}
QFrame#dropzone {{ background: {c['surface']}; border: 2px dashed {c['border_strong']}; border-radius: 16px; }}
QFrame#dropzone[active="true"] {{ border-color: {c['accent']}; background: {c['selection']}; }}
QFrame#banner {{ background: {c['warn_bg']}; border: 1px solid {c['warn_border']}; border-radius: 9px; }}
QFrame#banner QLabel {{ color: {c['warn_text']}; }}

QPushButton {{ background: {c['surface']}; border: 1px solid {c['border_strong']}; border-radius: 8px;
               padding: 8px 16px; min-height: 22px; }}
QPushButton:hover {{ background: {c['hover']}; }}
QPushButton:pressed {{ background: {c['selection']}; }}
QPushButton:disabled {{ color: {c['muted']}; border-color: {c['border']}; background: {c['bg']}; }}
QPushButton:checked {{ background: {c['selection']}; border-color: {c['accent']}; }}
QPushButton#primary {{ background: {c['accent']}; color: white; border: 1px solid {c['accent']};
                       font-weight: 700; padding: 11px 26px; }}
QPushButton#primary:hover {{ background: {c['accent_hover']}; border-color: {c['accent_hover']}; }}
QPushButton#primary:disabled {{ background: {c['accent_off']}; border-color: {c['accent_off']}; color: #eef2fb; }}
QPushButton#link {{ background: transparent; border: none; color: {c['accent']}; padding: 6px 8px; }}
QPushButton#link:hover {{ background: {c['hover']}; }}
QPushButton#rowbtn {{ padding: 5px 12px; min-height: 18px; }}

QLineEdit, QPlainTextEdit {{ background: {c['surface']}; border: 1px solid {c['border_strong']}; border-radius: 8px;
                             padding: 7px 10px; selection-background-color: {c['accent']}; selection-color: white; }}
QLineEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {c['accent']}; }}
QLineEdit:read-only {{ background: {c['alt']}; }}
QPlainTextEdit {{ font-family: "DejaVu Sans Mono", monospace; font-size: 9pt; }}
QComboBox {{ min-height: 24px; padding: 5px 10px; }}

QAbstractItemView {{ outline: 0; }}
QTreeView, QTableView {{ background: {c['surface']}; alternate-background-color: {c['alt']};
                         border: 1px solid {c['border']}; border-radius: 10px; gridline-color: transparent;
                         selection-background-color: {c['selection']}; selection-color: {c['text']}; }}
QTreeView::item, QTableView::item {{ padding: 3px 6px; border: none; }}
QTreeView::item:selected, QTableView::item:selected {{ background: {c['selection']}; color: {c['text']}; }}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{ background: {c['header']}; color: {c['muted']}; padding: 9px 10px; border: none;
                        border-bottom: 1px solid {c['border']}; font-weight: 700; }}
QTableView QTableCornerButton::section {{ background: {c['header']}; border: none; }}

QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {c['handle']}; border-radius: 4px; min-height: 40px; }}
QScrollBar::handle:horizontal {{ background: {c['handle']}; border-radius: 4px; min-width: 40px; }}
QScrollBar::handle:hover {{ background: {c['muted']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollArea {{ background: transparent; border: none; }}

QProgressBar {{ background: {c['border']}; border: none; border-radius: 4px; min-height: 8px; max-height: 8px; }}
QProgressBar::chunk {{ background: {c['accent']}; border-radius: 4px; }}
QToolTip {{ background: {c['surface']}; color: {c['text']}; border: 1px solid {c['border_strong']}; padding: 5px; }}
QCheckBox, QRadioButton {{ spacing: 8px; }}
QSplitter::handle {{ background: transparent; }}
"""


def apply(app, mode="system"):
    """Install style, font, palette and stylesheet. Returns the resolved mode ('light' or 'dark')."""
    global _style_ref
    if _style_ref is None:
        _style_ref = AppStyle()
        app.setStyle(_style_ref)
        families = QFontDatabase.families()
        family = "Roboto" if "Roboto" in families else ("Noto Sans" if "Noto Sans" in families else "DejaVu Sans")
        font = QFont(family)
        font.setPointSizeF(11)
        app.setFont(font)
    resolved = resolve(mode)
    c = DARK if resolved == "dark" else LIGHT
    app.setPalette(_palette(c))
    app.setStyleSheet(stylesheet(c))
    return resolved
