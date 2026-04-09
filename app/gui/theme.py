"""Переключение темы интерфейса (тёмная / светлая) для QApplication."""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

SETTINGS_ORG = "AudioGenerationSuite"
SETTINGS_APP = "AudioGenerationSuite"
KEY_THEME = "ui/theme"

THEME_DARK = "dark"
THEME_LIGHT = "light"


def load_theme_preference() -> str:
    s = QSettings(SETTINGS_ORG, SETTINGS_APP)
    v = s.value(KEY_THEME, THEME_DARK)
    return str(v) if v is not None else THEME_DARK


def save_theme_preference(theme: str) -> None:
    s = QSettings(SETTINGS_ORG, SETTINGS_APP)
    s.setValue(KEY_THEME, theme)


def _fusion_light_palette() -> QPalette:
    """Светлая тема: белые области ввода, тёмный текст, не «серая каша»."""
    from PySide6.QtCore import Qt

    # Фон окна — тёплый светло-серый; поля (Base) — белые, чтобы читалось как «светлая UI».
    window_bg = QColor(245, 245, 245)
    white = QColor(255, 255, 255)
    text = QColor(33, 33, 33)
    muted = QColor(115, 115, 115)

    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, window_bg)
    p.setColor(QPalette.ColorRole.WindowText, text)
    p.setColor(QPalette.ColorRole.Base, white)
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(237, 237, 237))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    p.setColor(QPalette.ColorRole.ToolTipText, text)
    p.setColor(QPalette.ColorRole.Text, text)
    p.setColor(QPalette.ColorRole.Button, QColor(236, 236, 236))
    p.setColor(QPalette.ColorRole.ButtonText, text)
    p.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    p.setColor(QPalette.ColorRole.Link, QColor(0, 102, 204))
    p.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.PlaceholderText, muted)
    # Рамки и отступы у Fusion
    p.setColor(QPalette.ColorRole.Light, white)
    p.setColor(QPalette.ColorRole.Midlight, QColor(250, 250, 250))
    p.setColor(QPalette.ColorRole.Mid, QColor(204, 204, 204))
    p.setColor(QPalette.ColorRole.Dark, QColor(180, 180, 180))
    p.setColor(QPalette.ColorRole.Shadow, QColor(90, 90, 90))

    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, muted)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, muted)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, muted)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(250, 250, 250))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor(240, 240, 240))
    return p


def _fusion_dark_palette() -> QPalette:
    from PySide6.QtCore import Qt

    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    p.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(127, 127, 127))
    disabled = QColor(127, 127, 127)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)
    return p


def apply_theme(app: QApplication, theme: str) -> None:
    fusion = QStyleFactory.create("Fusion")
    if fusion is None:
        return
    app.setStyle(fusion)
    if theme == THEME_LIGHT:
        app.setPalette(_fusion_light_palette())
    else:
        app.setPalette(_fusion_dark_palette())
