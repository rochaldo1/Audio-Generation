import sys

from PySide6.QtWidgets import QApplication

from app.gui.main_window import MainWindow
from app.gui.theme import apply_theme, load_theme_preference


def main() -> None:
    app = QApplication(sys.argv)
    apply_theme(app, load_theme_preference())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

