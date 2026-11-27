"""Dubbed audio track for YouTube multi-language audio.

dub.py <id> <lang>   (lang: es, pt, fr)

Reads the translated lines in scripts/dub/<id>.<lang>.json (one line per sentence of
out/<id>/timeline.json), speaks each with Kokoro and places it at the same time as the
English sentence, so the track lines up with the pictures. A line that is too long is
spoken faster (up to 1.3x), then squeezed with atempo as a last resort. Music bed and
loudness follow docs/audio.md. Writes out/<id>/dub/<id>-<lang>.m4a and a report.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from common import MODELS, OUT, ROOT, fail, load_json, log, save_json
from shots import DUCK_RATIO, MASTER_LUFS, MASTER_TP, MUSIC_UNDER_VOICE_DB, VOICE_LUFS

VOICES = {"es": ("em_alex", "es"), "pt": ("pm_alex", "pt-br"), "fr": ("ff_siwis", "fr-fr"),
          "it": ("im_nicola", "it")}
SR = 24000
BASE_SPEED = 0.95
MAX_SPEED = 1.3
GAP = 0.12


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    ap.add_argument("lang")
    a = ap.parse_args()
    from kokoro_onnx import Kokoro
    voice, lang = VOICES[a.lang]
    tl = load_json(OUT / a.vid / "timeline.json")
    sents, duration = tl["sentences"], tl["duration"]
    tr = load_json(ROOT / "scripts" / "dub" / f"{a.vid}.{a.lang}.json")
    lines = tr.get("lines") if tr else None
    if not lines or len(lines) != len(sents):
        fail(f"translation has {len(lines or [])} lines, timeline has {len(sents)}")
    k = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    track = np.zeros(int((duration + 2) * SR), dtype=np.float32)
    report = {"lang": a.lang, "voice": voice, "faster": 0, "squeezed": 0, "overflow_s": 0.0}
    tmp = OUT / a.vid / "dub" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    for i, (s, text) in enumerate(zip(sents, lines)):
        nxt = sents[i + 1]["start"] if i + 1 < len(sents) else duration
        slot = max(0.5, nxt - s["start"] - GAP)
        audio, sr = k.create(text, voice=voice, speed=BASE_SPEED, lang=lang)
        audio = np.asarray(audio, dtype=np.float32)
        if len(audio) / sr > slot:
            speed = min(MAX_SPEED, BASE_SPEED * (len(audio) / sr) / slot * 1.02)
            audio = np.asarray(k.create(text, voice=voice, speed=speed, lang=lang)[0], dtype=np.float32)
            report["faster"] += 1
        if len(audio) / sr > slot:
            ratio = min(2.0, (len(audio) / sr) / slot)
            src, dst = tmp / "in.wav", tmp / "out.wav"
            sf.write(src, audio, sr)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", f"atempo={ratio:.3f}",
                            str(dst)], check=True)
            audio, _ = sf.read(dst, dtype="float32")
            report["squeezed"] += 1
            report["overflow_s"] += max(0.0, len(audio) / sr - slot)
        a0 = int(s["start"] * SR)
        seg = audio[: max(0, len(track) - a0)]
        track[a0:a0 + len(seg)] += seg
    narr = OUT / a.vid / "dub" / f"narration-{a.lang}.wav"
    sf.write(narr, track[: int(duration * SR)], SR)

    out = OUT / a.vid / "dub" / f"{a.vid}-{a.lang}.m4a"
    music = load_json(OUT / a.vid / "music.json", {})
    mfile = ROOT / "assets" / "music" / Path(music.get("file", "")).name if music else None
    if mfile and mfile.exists():
        filt = (f"[1:a]atrim=0:{duration:.2f},afade=t=in:d=4,afade=t=out:st={max(0, duration - 6):.2f}:d=6,"
                f"aresample=48000,aformat=channel_layouts=mono,loudnorm=I={VOICE_LUFS}:TP=-2:LRA=11,"
                f"volume={MUSIC_UNDER_VOICE_DB}dB[m];"
                f"[0:a]aresample=48000,aformat=channel_layouts=mono,loudnorm=I={VOICE_LUFS}:TP=-2:LRA=11,asplit[n1][n2];"
                f"[m][n2]sidechaincompress=threshold=0.05:ratio={DUCK_RATIO}:attack=60:release=900[md];"
                f"[n1][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I={MASTER_LUFS}:TP={MASTER_TP}:LRA=11,"
                f"aresample=48000[aout]")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(narr), "-stream_loop", "-1", "-i", str(mfile),
               "-filter_complex", filt, "-map", "[aout]"]
    else:
        log("dub: no music bed found, voice only")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(narr),
               "-af", f"loudnorm=I={MASTER_LUFS}:TP={MASTER_TP}:LRA=11,aresample=48000"]
    subprocess.run(cmd + ["-c:a", "aac", "-b:a", "128k", "-t", f"{duration:.3f}", str(out)], check=True)
    report["overflow_s"] = round(report["overflow_s"], 1)
    save_json(OUT / a.vid / "dub" / f"report-{a.lang}.json", report)
    log(f"dub {a.vid} {a.lang}: {out.name}, {report}")


if __name__ == "__main__":
    main()
