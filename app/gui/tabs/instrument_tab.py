from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.gui.generation_worker import GenerationKind, GenerationResult, GenerationWorker
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
            QMessageBox.warning(self, "Ошибка", "Сначала создайте или выберите проект.")
            return

        params = GenerationParams(
            prompt=self.prompt_edit.toPlainText().strip() or "instrumental music",
            duration_seconds=self.duration_spin.value(),
            tempo_bpm=self.tempo_spin.value(),
            genre=self.genre_combo.currentText() or None,
            arrangement_density=self.density_combo.currentText(),
            structure_complexity=self.complexity_combo.currentText(),
        )

        def task():
            track = mw.generation_controller.generate_instrumental(project, params)
            return GenerationResult(kind=GenerationKind.INSTRUMENTAL, success=True, track=track)

        self._run_generation(task, "Генерация инструментала...", self.btn_generate)

    def _on_variation_clicked(self) -> None:
        mw = self.main_window
        project = mw.current_project
        if project is None or not project.track_versions:
            QMessageBox.warning(self, "Ошибка", "Сначала создайте проект и сгенерируйте трек.")
            return
        base_track = project.track_versions[-1]

        def task():
            track = mw.generation_controller.create_variation(project, base_track)
            return GenerationResult(kind=GenerationKind.VARIATION, success=True, track=track)

        self._run_generation(task, "Создание вариации...", self.btn_variation)

    def _run_generation(
        self,
        task,
        label: str,
        button: QPushButton,
    ) -> None:
        button.setEnabled(False)

        thread = QThread(self)
        worker = GenerationWorker(task)
        worker.moveToThread(thread)
        thread.finished.connect(thread.deleteLater)

        # Сохраняем ссылки, чтобы объекты не были собраны GC,
        # пока идёт генерация (иначе сигнал finished может не дойти).
        self._current_progress = None
        self._current_thread = thread
        self._current_worker = worker

        def _thread_cleanup():
            self._current_progress = None
            self._current_thread = None
            self._current_worker = None

        thread.finished.connect(_thread_cleanup)

        def on_finished(result: GenerationResult):
            button.setEnabled(True)
            thread.quit()
            if result.success and result.track:
                mw = self.main_window
                mw.project_tab.refresh()
                mw.playback_controller.play_track(result.track)
            elif result.error:
                QMessageBox.critical(self, "Ошибка генерации", result.error)

        worker.finished.connect(on_finished)
        thread.started.connect(worker.run)
        thread.start()

