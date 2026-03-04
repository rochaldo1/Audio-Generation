from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf


class MixService:
    """
    Simple mixing service to combine instrumental and vocal tracks into a single WAV.
    """

    def mix_tracks(
        self,
        instrumental_path: Path,
        vocal_path: Path,
        output_path: Path,
        vocal_gain: float = 0.0,
    ) -> Path:
        """
        Mix instrumental and vocal WAV files with basic normalization.
        """
        instr_audio, sr_instr = sf.read(str(instrumental_path))
        vocal_audio, sr_vocal = sf.read(str(vocal_path))

        if sr_instr != sr_vocal:
            raise ValueError("Sample rates of instrumental and vocal tracks must match.")

        # Ensure both tracks have the same length by padding or trimming.
        max_len = max(instr_audio.shape[0], vocal_audio.shape[0])
        instr_audio = self._pad_or_trim(instr_audio, max_len)
        vocal_audio = self._pad_or_trim(vocal_audio, max_len)

        # Convert vocal_gain from dB to linear if needed; here we treat it as dB.
        gain_linear = 10 ** (vocal_gain / 20.0)
        mix = instr_audio + gain_linear * vocal_audio

        # Normalize to avoid clipping.
        peak = np.max(np.abs(mix))
        if peak > 1.0:
            mix = mix / peak

        sf.write(str(output_path), mix, samplerate=sr_instr)
        return output_path

    @staticmethod
    def _pad_or_trim(audio: np.ndarray, target_len: int) -> np.ndarray:
        if audio.shape[0] == target_len:
            return audio
        if audio.shape[0] > target_len:
            return audio[:target_len]
        pad_width = target_len - audio.shape[0]
        if audio.ndim == 1:
            pad = np.zeros(pad_width, dtype=audio.dtype)
        else:
            pad = np.zeros((pad_width, audio.shape[1]), dtype=audio.dtype)
        return np.concatenate([audio, pad], axis=0)

