"""Tasarım tuvalindeki renkler ve Qt stil sayfası (QSS).

Renkler docs/tasarim/*.dc.html dosyalarıyla birebir aynıdır.
"""

# Renk paleti
BG = "#f6f7f8"
SURFACE = "#ffffff"
BORDER = "#e3e6e9"
BORDER_STRONG = "#c9cdd2"
TEXT = "#1c1f23"
TEXT_MUTED = "#6b7280"
TEXT_SOFT = "#4b5563"
ACCENT = "#2f6f9f"
ACCENT_DARK = "#245678"
ACCENT_SOFT = "#e6eff6"
SUCCESS = "#166534"
SUCCESS_SOFT = "#e7f5ea"
WARN = "#7a5a00"
WARN_SOFT = "#fff8e6"
WARN_BORDER = "#f1dfae"
DANGER = "#b91c1c"
INPUT_BG = "#fbfbfc"

STYLESHEET = f"""
QMainWindow, QDialog {{ background: {BG}; }}
QWidget {{ color: {TEXT}; font-family: "Segoe UI"; font-size: 10pt; }}

/* Kenar çubuğu */
#Sidebar {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
#Sidebar QPushButton {{
    text-align: left; padding: 10px 12px; border: none; border-radius: 6px;
    color: {TEXT_SOFT}; font-size: 10.5pt; background: transparent;
}}
#Sidebar QPushButton:hover {{ background: {BG}; }}
#Sidebar QPushButton:checked {{ background: {ACCENT_SOFT}; color: {ACCENT_DARK}; font-weight: 600; }}
#SidebarFooter {{ color: {TEXT_MUTED}; font-size: 9pt; }}

/* Kartlar */
QFrame#Card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
QFrame#StatTile {{ background: {BG}; border-radius: 6px; }}
QFrame#StatCard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
QFrame#DropZone {{ background: {SURFACE}; border: 2px dashed #b9c0c8; border-radius: 10px; }}
QFrame#DropZone[active="true"] {{ border-color: {ACCENT}; background: {ACCENT_SOFT}; }}
QFrame#WarnBanner {{ background: {WARN_SOFT}; border: 1px solid {WARN_BORDER}; border-radius: 8px; }}
QFrame#InfoBanner {{ background: #eef4f9; border-radius: 6px; }}

/* Metinler */
QLabel#H1 {{ font-size: 18pt; font-weight: 600; }}
QLabel#H2 {{ font-size: 16pt; font-weight: 600; }}
QLabel#Subtle {{ color: {TEXT_MUTED}; }}
QLabel#Soft {{ color: {TEXT_SOFT}; }}
QLabel#SectionTitle {{ font-weight: 600; }}
QLabel#TileLabel {{ color: {TEXT_MUTED}; font-size: 9pt; }}
QLabel#TileValue {{ font-weight: 600; font-size: 12pt; }}
QLabel#BigPercent {{ font-weight: 600; font-size: 15pt; }}
QLabel#WarnTitle {{ color: {WARN}; font-weight: 600; font-size: 9.5pt; }}
QLabel#InfoText {{ color: {ACCENT_DARK}; }}
QLabel#Pill {{ padding: 4px 10px; border-radius: 12px; font-size: 9pt; font-weight: 600; }}
QLabel#Pill[kind="success"] {{ background: {SUCCESS_SOFT}; color: {SUCCESS}; }}
QLabel#Pill[kind="warn"] {{ background: {WARN_SOFT}; color: {WARN}; }}
QLabel#Pill[kind="accent"] {{ background: {ACCENT_SOFT}; color: {ACCENT_DARK}; }}

/* Düğmeler */
QPushButton {{
    min-height: 40px; padding: 0 20px; border-radius: 6px;
    border: 1px solid {BORDER_STRONG}; background: {SURFACE}; font-weight: 600;
}}
QPushButton:hover {{ background: {BG}; }}
QPushButton:disabled {{ color: #9ca3af; background: {BG}; }}
QPushButton#Primary {{ background: {ACCENT}; color: white; border: none; min-height: 44px; padding: 0 24px; }}
QPushButton#Primary:hover {{ background: {ACCENT_DARK}; }}
QPushButton#Primary:disabled {{ background: #9fbad0; color: white; }}
QPushButton#Outline {{ color: {ACCENT}; border: 1px solid {ACCENT}; background: transparent; }}
QPushButton#Outline:hover {{ background: {ACCENT_SOFT}; }}
QPushButton#Danger {{ color: {DANGER}; border: 1px solid {DANGER}; background: transparent; min-height: 44px; }}
QPushButton#Danger:hover {{ background: #fdecec; }}
QPushButton#Link {{ border: none; background: transparent; color: {ACCENT}; min-height: 0; padding: 0; font-weight: 400; }}
QPushButton#Link:hover {{ color: {ACCENT_DARK}; text-decoration: underline; }}
QPushButton#Small {{ min-height: 36px; padding: 0 14px; font-size: 9.5pt; }}
QPushButton#SmallPrimary {{ min-height: 36px; padding: 0 14px; font-size: 9.5pt; background: {ACCENT}; color: white; border: none; }}
QPushButton#SmallPrimary:hover {{ background: {ACCENT_DARK}; }}

/* Girdiler */
QLineEdit {{
    min-height: 38px; padding: 0 12px; border: 1px solid {BORDER_STRONG};
    border-radius: 6px; background: {INPUT_BG}; color: {TEXT_SOFT};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QCheckBox {{ spacing: 8px; }}

/* İlerleme çubuğu */
QProgressBar {{ border: none; border-radius: 5px; background: {BORDER}; min-height: 10px; max-height: 10px; text-align: center; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 5px; }}

/* Tablo */
QTableWidget {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; gridline-color: transparent; }}
QTableWidget {{ font-size: 9.5pt; }}
QTableWidget::item {{ padding: 4px 8px; border-bottom: 1px solid #eef0f2; }}
QTableWidget::item:selected {{ background: {ACCENT_SOFT}; color: {TEXT}; }}
QHeaderView::section {{
    background: {BG}; color: {TEXT_MUTED}; font-weight: 600; font-size: 9pt;
    padding: 8px 8px; border: none; border-bottom: 1px solid {BORDER};
}}
QListWidget {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
QListWidget::item {{ padding: 10px 16px; border-bottom: 1px solid #eef0f2; }}
QListWidget::item:selected {{ background: {ACCENT_SOFT}; color: {TEXT}; }}

QScrollArea {{ border: none; background: transparent; }}
QToolTip {{ background: {TEXT}; color: white; border: none; padding: 6px; }}
"""
