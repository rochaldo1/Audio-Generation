from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List, Optional

import nnsvs  # type: ignore
import pysinsy  # type: ignore
from nnmnkwii.io import hts  # type: ignore

from app.models.project_models import VocalParams

# Простая мелодия по умолчанию: последовательность нот (step, octave, duration в divisions)
# A4, G4, A4, B4, A4... — простая волна вокруг A4
_DEFAULT_MELODY: List[tuple] = [
    ("A", 4, 4), ("G", 4, 4), ("A", 4, 4), ("B", 4, 4),
    ("A", 4, 4), ("G", 4, 4), ("E", 4, 4), ("E", 4, 4),
]


def _split_lyrics_to_tokens(lyrics: str) -> List[str]:
    """
    Разбивает текст на токены (слова или слоги) для привязки к нотам.
    Простой вариант: по пробелам и переносам строк.
    """
    if not lyrics or not lyrics.strip():
        return ["la"]  # fallback
    tokens: List[str] = []
    for line in lyrics.strip().splitlines():
        for word in line.split():
            if word:
                tokens.append(word)
    return tokens if tokens else ["la"]


def _generate_musicxml(
    tokens: List[str],
    tempo_bpm: int = 120,
    divisions: int = 4,
) -> str:
    """
    Генерирует минимальный MusicXML с текстом и простой мелодией.
    В каждом такте 4/4: пауза(4) + ноты по 4 единицы (quarter) каждая.
    В один такт помещаем до 3 нот (4+3*4=16).
    """
    melody = _DEFAULT_MELODY * (len(tokens) // len(_DEFAULT_MELODY) + 1)
    measures: List[str] = []
    idx = 0
    measure_num = 1

    while idx < len(tokens):
        # Начальная пауза только в первом такте
        if measure_num == 1:
            measure_notes = [
                '      <note><rest/><duration>4</duration><voice>1</voice></note>'
            ]
        else:
            measure_notes = []

        # До 3 нот на такт (остаток заполняем до 16)
        count = 0
        units_used = 4 if measure_num == 1 else 0
        while idx < len(tokens) and count < 3 and units_used + 4 <= 16:
            step, octave, dur = melody[idx % len(melody)]
            token = _escape_xml(tokens[idx])
            measure_notes.append(f"""      <note>
        <pitch><step>{step}</step><octave>{octave}</octave></pitch>
        <duration>4</duration><voice>1</voice><type>quarter</type>
        <lyric><syllabic>single</syllabic><text>{token}</text></lyric>
      </note>""")
            idx += 1
            count += 1
            units_used += 4

        # Конечная пауза в последнем такте (pysinsy ожидает rest в конце)
        if idx >= len(tokens):
            measure_notes.append(
                '      <note><rest/><duration>4</duration><voice>1</voice></note>'
            )
            units_used += 4
        # Дополняем такт до 16 паузами
        while units_used < 16:
            measure_notes.append(
                '      <note><rest/><duration>4</duration><voice>1</voice></note>'
            )
            units_used += 4

        attrs = ""
        if measure_num == 1:
            attrs = f"""      <attributes>
        <divisions>{divisions}</divisions>
        <time><beats>4</beats><beat-type>4</beat-type></time>
      </attributes>
      <sound tempo="{tempo_bpm}"/>"""
        measures.append(f"""    <measure number="{measure_num}">
{attrs}
{chr(10).join(measure_notes)}
    </measure>""")
        measure_num += 1

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
    "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <part-list>
    <score-part id="P1"><part-name>P1</part-name></score-part>
  </part-list>
  <part id="P1">
{chr(10).join(measures)}
  </part>
</score-partwise>
'''


def _escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_demo_labels() -> hts.HTSLabelFile:
    """
    Build HTS labels using the built-in NIT-song070 demo score.
    """
    xml_path = nnsvs.util.example_xml_file("song070_f00001_063")
    contexts = pysinsy.extract_fullcontext(xml_path)
    labels = hts.HTSLabelFile.create_from_contexts(contexts)
    return labels


def build_labels_from_lyrics(
    params: VocalParams,
    tempo_bpm: Optional[int] = None,
) -> hts.HTSLabelFile:
    """
    Convert VocalParams (lyrics etc.) to HTS labels.

    Generates a minimal MusicXML score with user lyrics and a simple
    melodic template, then uses pysinsy to extract HTS full-context labels.
    Falls back to demo labels if extraction fails (e.g. empty lyrics).
    """
    lyrics = (params.lyrics or "").strip()
    if not lyrics:
        return build_demo_labels()

    tokens = _split_lyrics_to_tokens(lyrics)
    if not tokens:
        return build_demo_labels()

    tempo = tempo_bpm or 120
    xml_str = _generate_musicxml(tokens, tempo_bpm=tempo)

    with tempfile.NamedTemporaryFile(
        suffix=".xml", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(xml_str)
        xml_path = Path(f.name)

    try:
        contexts = pysinsy.extract_fullcontext(str(xml_path))
        labels = hts.HTSLabelFile.create_from_contexts(contexts)
        return labels
    except Exception:
        return build_demo_labels()
    finally:
        xml_path.unlink(missing_ok=True)

