"""FFmpeg render pipeline. Combineert b-roll + voice + music + ASS-subtitles
naar een 1080x1920 MP4. Gebruikt FFmpeg subprocess direct (sneller dan MoviePy).
"""

import subprocess
import shutil
from pathlib import Path
from typing import Sequence


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("FFmpeg niet gevonden in PATH. Install: winget install Gyan.FFmpeg")
    return exe


def _ffprobe_duration(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def normalize_clip(input_path: Path, output_path: Path, duration: float, width: int = 1080, height: int = 1920) -> Path:
    """Schaalt + croppt + trimt 1 clip naar 1080x1920, exact `duration` seconden."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        _ffmpeg(), "-y", "-i", str(input_path),
        "-t", f"{duration:.2f}",
        "-vf", (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1,fps=30"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def concat_clips(clips: Sequence[Path], target_duration: float, work_dir: Path) -> Path:
    """Trimt clips zodat hun totaal `target_duration` is, schikt op rotatie."""
    work_dir.mkdir(parents=True, exist_ok=True)
    if not clips:
        raise ValueError("Geen clips om te concatten")

    per_clip = target_duration / len(clips)
    normalized = []
    for i, c in enumerate(clips):
        n = work_dir / f"norm_{i:02d}.mp4"
        normalize_clip(c, n, duration=per_clip + 0.5)  # iets extra voor concat-safety
        normalized.append(n)

    # Concat via demuxer (geen re-encode mogelijk maar veiliger met re-encode)
    list_path = work_dir / "concat.txt"
    list_path.write_text("\n".join(f"file '{p.as_posix()}'" for p in normalized), encoding="utf-8")

    out = work_dir / "concat.mp4"
    cmd = [
        _ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-t", f"{target_duration:.2f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def render_final(
    video_track: Path,
    voice_mp3: Path,
    music_mp3: Path | None,
    ass_subs: Path | None,
    output_path: Path,
    music_volume_db: int = -28,
) -> Path:
    """Combineert video + voice (0 dB) + music (-20 dB) + subtitles → final MP4."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Bouw filter_complex - voice prominent, music zacht eronder, daarna loudnorm voor TikTok
    if music_mp3 and music_mp3.exists():
        audio_filter = (
            f"[1:a]volume=2.5,loudnorm=I=-14:TP=-1.5:LRA=11[voice];"
            f"[2:a]aloop=loop=-1:size=2e9,volume={10 ** (music_volume_db / 20):.4f}[music];"
            f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2,"
            f"loudnorm=I=-14:TP=-1.5:LRA=11[a]"
        )
        inputs = ["-i", str(video_track), "-i", str(voice_mp3), "-i", str(music_mp3)]
    else:
        audio_filter = "[1:a]volume=2.5,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
        inputs = ["-i", str(video_track), "-i", str(voice_mp3)]

    if ass_subs and ass_subs.exists():
        # Escape pad voor FFmpeg subtitles filter (Windows backslashes + colons)
        ass_str = str(ass_subs).replace("\\", "/").replace(":", "\\:")
        video_filter = f"[0:v]subtitles='{ass_str}'[v]"
    else:
        video_filter = "[0:v]copy[v]"

    filter_complex = f"{video_filter};{audio_filter}"

    cmd = [
        _ffmpeg(), "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed:\n{proc.stderr[-2000:]}")
    return output_path


def assemble_video(
    clips: list[Path],
    voice_mp3: Path,
    music_mp3: Path | None,
    ass_subs: Path | None,
    output_path: Path,
    work_dir: Path,
    music_volume_db: int = -28,
) -> Path:
    """High-level: concat clips → mix met audio + subs → finale MP4.
    Lengte = duur van voice + 1 sec uitloop."""
    voice_dur = _ffprobe_duration(voice_mp3)
    target = voice_dur + 1.0

    if not clips:
        raise ValueError("Geen b-roll clips")

    video_track = concat_clips(clips, target_duration=target, work_dir=work_dir)
    return render_final(video_track, voice_mp3, music_mp3, ass_subs, output_path, music_volume_db)


if __name__ == "__main__":
    print("Render module loaded. Use via run_week.py.")
