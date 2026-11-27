"""Narration: Kokoro (open source, runs locally on CPU, free).

Writes out/<id>/narration.wav, out/<id>/timeline.json and out/<id>/<id>.srt.
Every sentence is synthesized separately so subtitle timings are exact.
"""
from __future__ import annotations

import argparse

import numpy as np
import soundfile as sf

from common import MODELS, OUT, find_script, log, parse_script, save_json, split_sentences, fail

SR = 24000
PAUSE_SENT = 0.35
PAUSE_PAR = 0.8
PAUSE_SECTION = 1.6
LEAD_IN = 1.0


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def wrap_caption(text: str, width: int = 42) -> list[str]:
    """Split a sentence into caption chunks of at most two lines."""
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 > width and line:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        lines.append(line)
    return ["\n".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    args = ap.parse_args()

    from kokoro_onnx import Kokoro

    script = parse_script(find_script(args.vid))
    voice = script.meta.get("voice", "bm_george")
    speed = float(script.meta.get("speed", 0.92))
    lang = "en-gb" if voice.startswith("b") else "en-us"
    model = MODELS / "kokoro-v1.0.onnx"
    voices = MODELS / "voices-v1.0.bin"
    if not model.exists() or not voices.exists():
        fail("Kokoro model files missing in models/ (run pipeline/get_models.sh)")
    kokoro = Kokoro(str(model), str(voices))

    out_dir = OUT / script.vid
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks: list[np.ndarray] = [np.zeros(int(LEAD_IN * SR), dtype=np.float32)]
    t = LEAD_IN
    timeline = {"sections": [], "sample_rate": SR}
    cues: list[tuple[float, float, str]] = []

    for sec in script.sections:
        sec_start = t
        for pi, par in enumerate(sec.paragraphs):
            for sent in split_sentences(par):
                audio, sr = kokoro.create(sent, voice=voice, speed=speed, lang=lang)
                if sr != SR:
                    fail(f"unexpected sample rate {sr}")
                audio = audio.astype(np.float32)
                dur = len(audio) / SR
                parts = wrap_caption(sent)
                total_chars = sum(len(p) for p in parts)
                ct = t
                for p in parts:
                    pd = dur * len(p) / total_chars
                    cues.append((ct, ct + pd, p))
                    ct += pd
                chunks.append(audio)
                t += dur
                chunks.append(np.zeros(int(PAUSE_SENT * SR), dtype=np.float32))
                t += PAUSE_SENT
            if pi < len(sec.paragraphs) - 1:
                chunks.append(np.zeros(int(PAUSE_PAR * SR), dtype=np.float32))
                t += PAUSE_PAR
        chunks.append(np.zeros(int(PAUSE_SECTION * SR), dtype=np.float32))
        t += PAUSE_SECTION
        timeline["sections"].append(
            {"index": sec.index, "title": sec.title, "images": sec.image_keys,
             "start": round(sec_start, 3), "end": round(t, 3)}
        )
        log(f"tts section {sec.index} '{sec.title}' {t - sec_start:.1f}s")

    audio = np.concatenate(chunks)
    peak = float(np.max(np.abs(audio))) or 1.0
    audio = (audio / peak * 0.89).astype(np.float32)
    sf.write(out_dir / "narration.wav", audio, SR)
    timeline["duration"] = round(len(audio) / SR, 3)
    save_json(out_dir / "timeline.json", timeline)

    with open(out_dir / f"{script.vid}.srt", "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n")
    log(f"narration {timeline['duration'] / 60:.1f} min, {len(cues)} captions, {script.word_count} words")


if __name__ == "__main__":
    main()
