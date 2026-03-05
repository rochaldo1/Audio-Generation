from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.gui.generation_worker import GenerationKind, GenerationResult, GenerationWorker
from app.models.project_models import GenerationParams, VocalParams


class VocalTab(QWidget):
    def __init__(self, main_window: "MainWindow") -> None:  # type: ignore[name-defined]
        super().__init__(main_window)
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.lyrics_edit = QTextEdit()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 300)
        self.duration_spin.setValue(30)
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["default"])

        self.style_combo = QComboBox()
        self.style_combo.addItems(["neutral", "soft", "powerful"])

        self.delivery_combo = QComboBox()
        self.delivery_combo.addItems(["legato", "staccato", "mixed"])

        self.intensity_spin = QSpinBox()
        self.intensity_spin.setRange(0, 100)
        self.intensity_spin.setValue(50)

        form.addRow("Текст песни:", self.lyrics_edit)
        form.addRow("Длительность трека (сек):", self.duration_spin)
        form.addRow("Голос:", self.voice_combo)
        form.addRow("Стиль исполнения:", self.style_combo)
        form.addRow("Манера подачи:", self.delivery_combo)
        form.addRow("Интенсивность:", self.intensity_spin)

        layout.addLayout(form)

        self.btn_generate_vocal = QPushButton("Сгенерировать песню (музыка + вокал)")
        layout.addWidget(self.btn_generate_vocal)

        info = QLabel(
            "Введите текст песни (слова через пробел). "
            "Модель r9y9/yoko_latest обучена на японском — для лучшего качества используйте японский текст или ромадзи."
        )
        layout.addWidget(info)

        self.btn_generate_vocal.clicked.connect(self._on_generate_clicked)

    def _on_generate_clicked(self) -> None:
        mw = self.main_window
        project = mw.current_project
        if project is None:
            QMessageBox.warning(self, "Ошибка", "Сначала создайте или выберите проект.")
            return

        vocal_params = VocalParams(
            lyrics=self.lyrics_edit.toPlainText().strip() or "la la la",
            voice_id=self.voice_combo.currentText(),
            style=self.style_combo.currentText(),
            delivery=self.delivery_combo.currentText(),
            intensity=self.intensity_spin.value() / 100.0,
            enable_background_voices=False,
        )

        gen_params = GenerationParams(
            prompt="vocal song",
            duration_seconds=self.duration_spin.value(),
        )

        def task():
            track = mw.generation_controller.generate_vocal(project, vocal_params, gen_params)
            return GenerationResult(kind=GenerationKind.VOCAL, success=True, track=track)

        self._run_generation(task, "Генерация вокала...", self.btn_generate_vocal)

    def _run_generation(self, task, label: str, button: QPushButton) -> None:
        button.setEnabled(False)

        thread = QThread(self)
        worker = GenerationWorker(task)
        worker.moveToThread(thread)
        thread.finished.connect(thread.deleteLater)

        def _thread_cleanup():
            self._current_progress = None
            self._current_thread = None
            self._current_worker = None

        thread.finished.connect(_thread_cleanup)

        # Не даём Qt/Python уничтожить объекты, пока идёт генерация.
        self._current_progress = None
        self._current_thread = thread
        self._current_worker = worker

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

