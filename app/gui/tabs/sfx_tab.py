from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.project_models import SfxParams


class SfxTab(QWidget):
    def __init__(self, main_window: "MainWindow") -> None:  # type: ignore[name-defined]
        super().__init__(main_window)
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.prompt_edit = QTextEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["atmosphere", "short_sfx", "transition", "background"])

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 30)
        self.duration_spin.setValue(5)

        form.addRow("Описание эффекта:", self.prompt_edit)
        form.addRow("Тип эффекта:", self.type_combo)
        form.addRow("Длительность (сек):", self.duration_spin)

        layout.addLayout(form)

        self.btn_generate = QPushButton("Сгенерировать SFX")
        layout.addWidget(self.btn_generate)

        self.btn_generate.clicked.connect(self._on_generate_clicked)

    def _on_generate_clicked(self) -> None:
        mw = self.main_window
        project = mw.current_project
        if project is None:
            return

        params = SfxParams(
            prompt=self.prompt_edit.toPlainText().strip(),
            sfx_type=self.type_combo.currentText(),
            duration_seconds=self.duration_spin.value(),
        )
        track = mw.generation_controller.generate_sfx(project, params)
        mw.project_tab.refresh()
        mw.playback_controller.play_track(track)

