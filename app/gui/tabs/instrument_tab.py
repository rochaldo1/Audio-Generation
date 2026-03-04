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

from app.models.project_models import GenerationParams


class InstrumentTab(QWidget):
    def __init__(self, main_window: "MainWindow") -> None:  # type: ignore[name-defined]
        super().__init__(main_window)
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.prompt_edit = QTextEdit()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 120)
        self.duration_spin.setValue(30)

        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["", "cinematic", "electronic", "rock", "pop"])

        self.density_combo = QComboBox()
        self.density_combo.addItems(["low", "medium", "high"])
        self.density_combo.setCurrentText("medium")

        self.complexity_combo = QComboBox()
        self.complexity_combo.addItems(["simple", "medium", "complex"])
        self.complexity_combo.setCurrentText("medium")

        self.tempo_spin = QSpinBox()
        self.tempo_spin.setRange(40, 220)
        self.tempo_spin.setValue(120)

        form.addRow("Описание (жанр, настроение, инструменты):", self.prompt_edit)
        form.addRow("Длительность (сек):", self.duration_spin)
        form.addRow("Жанр/стиль:", self.genre_combo)
        form.addRow("Плотность аранжировки:", self.density_combo)
        form.addRow("Сложность структуры:", self.complexity_combo)
        form.addRow("Темп (BPM):", self.tempo_spin)

        layout.addLayout(form)

        self.btn_generate = QPushButton("Сгенерировать инструментал")
        self.btn_variation = QPushButton("Создать вариацию")
        layout.addWidget(self.btn_generate)
        layout.addWidget(self.btn_variation)

        self.btn_generate.clicked.connect(self._on_generate_clicked)
        self.btn_variation.clicked.connect(self._on_variation_clicked)

    def _on_generate_clicked(self) -> None:
        mw = self.main_window
        project = mw.current_project
        if project is None:
            return

        params = GenerationParams(
            prompt=self.prompt_edit.toPlainText().strip(),
            duration_seconds=self.duration_spin.value(),
            tempo_bpm=self.tempo_spin.value(),
            genre=self.genre_combo.currentText() or None,
            arrangement_density=self.density_combo.currentText(),
            structure_complexity=self.complexity_combo.currentText(),
        )
        track = mw.generation_controller.generate_instrumental(project, params)
        mw.project_tab.refresh()
        mw.playback_controller.play_track(track)

    def _on_variation_clicked(self) -> None:
        mw = self.main_window
        project = mw.current_project
        if project is None or not project.track_versions:
            return
        base_track = project.track_versions[-1]
        track = mw.generation_controller.create_variation(project, base_track)
        mw.project_tab.refresh()
        mw.playback_controller.play_track(track)

