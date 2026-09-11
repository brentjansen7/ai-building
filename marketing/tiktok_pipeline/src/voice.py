"""edge-tts wrapper. Genereert MP3 vanuit voice-over tekst."""

import asyncio
import yaml
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yml"


def _load_voice_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["voice"]


async def _synthesize(text: str, output_path: Path, voice: str, rate: str, pitch: str):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(str(output_path))


def synthesize(text: str, output_path: str | Path, voice: str | None = None) -> Path:
    cfg = _load_voice_config()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chosen_voice = voice or cfg["primary"]
    asyncio.run(_synthesize(text, output_path, chosen_voice, cfg["rate"], cfg["pitch"]))
    return output_path


def script_to_voice_text(hook: str, body: str, cta: str) -> str:
    return f"{hook}. {body} {cta}"


if __name__ == "__main__":
    sample = "Een 16-jarige bouwde dit voor zijn eigen postroute. Ik plak 80 adressen, klik optimaliseer, en de route staat in 10 seconden klaar. Link in bio. Gratis proberen."
    out = ROOT / "cache" / "test_voice.mp3"
    p = synthesize(sample, out)
    print(f"Generated voice -> {p}")
