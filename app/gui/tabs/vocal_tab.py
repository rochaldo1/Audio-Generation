from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.project_models import TrackType, VocalParams


class VocalTab(QWidget):
    def __init__(self, main_window: "MainWindow") -> None:  # type: ignore[name-defined]
        super().__init__(main_window)
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.lyrics_edit = QTextEdit()
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
        form.addRow("Голос:", self.voice_combo)
        form.addRow("Стиль исполнения:", self.style_combo)
        form.addRow("Манера подачи:", self.delivery_combo)
        form.addRow("Интенсивность:", self.intensity_spin)

        layout.addLayout(form)

        self.btn_generate_vocal = QPushButton("Сгенерировать вокал (а капелла)")
        layout.addWidget(self.btn_generate_vocal)

        info = QLabel(
            "Примечание: NNSVSService пока является заглушкой.\n"
            "Для реальной генерации вокала нужно настроить модели NNSVS."
        )
        layout.addWidget(info)

        self.btn_generate_vocal.clicked.connect(self._on_generate_clicked)

    def _on_generate_clicked(self) -> None:
        # Placeholder: wiring to NNSVSService is not implemented yet.
        # Keep method to avoid GUI errors; actual synthesis will raise
        # NotImplementedError from NNSVSService.
        mw = self.main_window
        project = mw.current_project
        if project is None:
            return

        params = VocalParams(
            lyrics=self.lyrics_edit.toPlainText().strip(),
            voice_id=self.voice_combo.currentText(),
            style=self.style_combo.currentText(),
            delivery=self.delivery_combo.currentText(),
            intensity=self.intensity_spin.value() / 100.0,
            enable_background_voices=False,
        )
        try:
            # This will currently raise NotImplementedError.
            out_path = project.base_path / "vocal_placeholder.wav"
            mw.ctx.nnsvs_service.synthesize_vocals(params, out_path)
        except NotImplementedError:
            # In MVP we simply do nothing but keep the GUI functional.
            pass

