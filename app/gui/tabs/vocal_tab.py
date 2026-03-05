from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
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

        # Music (instrumental) parameters for the song
        self.music_prompt_edit = QTextEdit()
        self.music_genre_combo = QComboBox()
        self.music_genre_combo.addItems(["", "cinematic", "electronic", "rock", "pop"])

        self.music_density_combo = QComboBox()
        self.music_density_combo.addItems(["low", "medium", "high"])
        self.music_density_combo.setCurrentText("medium")

        self.music_complexity_combo = QComboBox()
        self.music_complexity_combo.addItems(["simple", "medium", "complex"])
        self.music_complexity_combo.setCurrentText("medium")

        self.music_tempo_spin = QSpinBox()
        self.music_tempo_spin.setRange(40, 220)
        self.music_tempo_spin.setValue(120)

        form.addRow("Описание музыки (жанр, настроение, инструменты):", self.music_prompt_edit)
        form.addRow("Жанр/стиль музыки:", self.music_genre_combo)
        form.addRow("Плотность аранжировки:", self.music_density_combo)
        form.addRow("Сложность структуры:", self.music_complexity_combo)
        form.addRow("Темп (BPM):", self.music_tempo_spin)

        # Vocal parameters (ACE-Step 1.5: стиль и манера задаются через промпт, выбора голоса нет)
        self.lyrics_edit = QTextEdit()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 300)
        self.duration_spin.setValue(30)

        self.style_combo = QComboBox()
        self.style_combo.addItems(["neutral", "soft", "powerful"])

        self.delivery_combo = QComboBox()
        self.delivery_combo.addItems(["legato", "staccato", "mixed"])

        self.intensity_spin = QSpinBox()
        self.intensity_spin.setRange(0, 100)
        self.intensity_spin.setValue(50)

        form.addRow("Текст песни:", self.lyrics_edit)
        form.addRow("Длительность трека (сек):", self.duration_spin)
        form.addRow("Стиль исполнения:", self.style_combo)
        form.addRow("Манера подачи:", self.delivery_combo)
        form.addRow("Интенсивность:", self.intensity_spin)

        self.background_voices_check = QCheckBox("Фоновые партии (backing vocals)")
        self.background_voices_check.setChecked(False)
        form.addRow("", self.background_voices_check)

        layout.addLayout(form)

        preset_row = QHBoxLayout()
        self.btn_save_preset = QPushButton("Сохранить пресет")
        self.btn_load_preset = QPushButton("Загрузить пресет")
        preset_row.addWidget(self.btn_save_preset)
        preset_row.addWidget(self.btn_load_preset)
        preset_row.addStretch()
        layout.addLayout(preset_row)

        self.btn_generate_vocal = QPushButton("Сгенерировать песню (музыка + вокал)")
        layout.addWidget(self.btn_generate_vocal)

        info = QLabel("Введите текст песни. Музыка и вокал будут сгенерированы одновременно.")
        layout.addWidget(info)

        self.btn_save_preset.clicked.connect(self._on_save_preset)
        self.btn_load_preset.clicked.connect(self._on_load_preset)
        self.btn_generate_vocal.clicked.connect(self._on_generate_clicked)

    def _on_save_preset(self) -> None:
        name, ok = QInputDialog.getText(
            self, "Сохранить пресет", "Имя пресета:", text=""
        )
        if not ok or not name or not name.strip():
            return
        vocal_params = VocalParams(
            lyrics=self.lyrics_edit.toPlainText().strip() or "la la la",
            style=self.style_combo.currentText(),
            delivery=self.delivery_combo.currentText(),
            intensity=self.intensity_spin.value() / 100.0,
            enable_background_voices=self.background_voices_check.isChecked(),
        )
        self.main_window.preset_repo.save_vocal_preset(name.strip(), vocal_params)
        QMessageBox.information(self, "Пресет сохранён", f'Пресет "{name.strip()}" сохранён.')

    def _on_load_preset(self) -> None:
        presets = self.main_window.preset_repo.list_presets("vocal")
        if not presets:
            QMessageBox.information(
                self, "Загрузить пресет",
                "Нет сохранённых вокальных пресетов.",
            )
            return
        name, ok = QInputDialog.getItem(
            self, "Загрузить пресет", "Выберите пресет:", presets, 0, False
        )
        if not ok or not name:
            return
        params = self.main_window.preset_repo.load_vocal_preset(name)
        if params is None:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить пресет.")
            return
        self.lyrics_edit.setPlainText(params.lyrics or "")
        self.style_combo.setCurrentText(params.style)
        self.delivery_combo.setCurrentText(params.delivery)
        self.intensity_spin.setValue(int(params.intensity * 100))
        self.background_voices_check.setChecked(params.enable_background_voices)

    def _on_generate_clicked(self) -> None:
        mw = self.main_window
        project = mw.current_project
        if project is None:
            QMessageBox.warning(self, "Ошибка", "Сначала создайте или выберите проект.")
            return

        vocal_params = VocalParams(
            lyrics=self.lyrics_edit.toPlainText().strip() or "la la la",
            style=self.style_combo.currentText(),
            delivery=self.delivery_combo.currentText(),
            intensity=self.intensity_spin.value() / 100.0,
            enable_background_voices=self.background_voices_check.isChecked(),
        )

        gen_params = GenerationParams(
            prompt=self.music_prompt_edit.toPlainText().strip() or "full song with vocals",
            duration_seconds=self.duration_spin.value(),
            tempo_bpm=self.music_tempo_spin.value(),
            genre=self.music_genre_combo.currentText() or None,
            arrangement_density=self.music_density_combo.currentText(),
            structure_complexity=self.music_complexity_combo.currentText(),
        )

        def task():
            track = mw.generation_controller.generate_vocal(project, vocal_params, gen_params)
            return GenerationResult(kind=GenerationKind.VOCAL, success=True, track=track)

        self._run_generation(task, "Генерация вокала...", self.btn_generate_vocal)

    def _run_generation(self, task, label: str, button: QPushButton) -> None:
        self.main_window.set_generation_state(True, label)
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
            self.main_window.set_generation_state(False)
            button.setEnabled(True)
            thread.quit()
            if result.success and result.track:
                mw = self.main_window
                mw.project_tab.refresh()
            elif result.error:
                QMessageBox.critical(self, "Ошибка генерации", result.error)

        worker.finished.connect(on_finished)
        thread.started.connect(worker.run)
        thread.start()

