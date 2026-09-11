"""Genereert ASS-subtitle bestand met word-by-word highlight uit een audio MP3.
Gebruik: faster-whisper voor woord-timings, ASS karaoke-style voor TikTok-look.
"""

from pathlib import Path

from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent

# Lazy: model wordt 1x geladen per Python-proces
_model: WhisperModel | None = None


def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def transcribe_with_words(mp3_path: Path) -> list[dict]:
    """Returns [{word, start, end}, ...]"""
    model = _get_model()
    segments, _ = model.transcribe(
        str(mp3_path),
        language="nl",
        word_timestamps=True,
        vad_filter=True,
    )
    words = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                words.append({"word": w.word.strip(), "start": w.start, "end": w.end})
    return words


def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ASS_HEADER = """[Script Info]
Title: TikTok Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Montserrat,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,4,2,2,80,80,420,1
Style: Highlight,Montserrat,72,&H0000FFFF,&H0000FFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,4,2,2,80,80,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def words_to_ass(words: list[dict], output_path: Path, group_size: int = 4) -> Path:
    """Bundel woorden in groepen van 'group_size'; per groep alle woorden zichtbaar
    maar het huidige woord highlighted (geel) via inline color tag."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [ASS_HEADER]

    if not words:
        output_path.write_text(ASS_HEADER, encoding="utf-8")
        return output_path

    for i in range(0, len(words), group_size):
        group = words[i:i + group_size]
        for j, w in enumerate(group):
            start = _format_ass_time(w["start"])
            end = _format_ass_time(w["end"])
            parts = []
            for k, gw in enumerate(group):
                if k == j:
                    # Geel highlight
                    parts.append(r"{\c&H0000FFFF&}" + gw["word"].upper() + r"{\c&H00FFFFFF&}")
                else:
                    parts.append(gw["word"].upper())
            text = " ".join(parts)
            lines.append(f"Dialogue: 0,{start},{end},Caption,,0,0,0,,{text}")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def mp3_to_ass(mp3_path: Path | str, ass_path: Path | str) -> Path:
    words = transcribe_with_words(Path(mp3_path))
    return words_to_ass(words, Path(ass_path))


if __name__ == "__main__":
    import sys
    mp3 = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "cache" / "test_voice.mp3"
    ass = mp3.with_suffix(".ass")
    p = mp3_to_ass(mp3, ass)
    print(f"Generated subtitles -> {p}")
