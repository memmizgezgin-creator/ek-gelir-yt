"""Blind voice test: the same paragraph read by Kokoro and by Chatterbox Turbo (DeepInfra).

Writes out/voice-test/A.mp3, B.mp3, ... with shuffled labels, plus key.json (which is which)
and costs.json. All clips are normalised to -16 LUFS so loudness does not bias the choice.
"""
from __future__ import annotations

import base64
import json
import os
import random
import subprocess
from pathlib import Path

import numpy as np
import requests
import soundfile as sf

from common import MODELS, OUT, log

TEXT = (
    "At the start of the twentieth century, every machine shop in the world had the same problem. "
    "Steel was getting harder. Machines were getting stronger. But the tool itself kept failing. "
    "Push it too fast and the edge began to glow, then it softened, and within minutes it was gone. "
    "Then an inventor in a small town in Indiana made something strange. "
    "When it was heated to a dull red, the temperature at which ordinary tool steel turns soft as butter, it stayed hard. "
    "So what happened to Stellite?"
)
DEST = OUT / "voice-test"
MODEL = "ResembleAI/chatterbox-turbo"
USD_PER_CHAR = 1.0 / 1_000_000


def kokoro(path: Path) -> None:
    from kokoro_onnx import Kokoro
    k = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    audio, sr = k.create(TEXT, voice="bm_george", speed=0.92, lang="en-gb")
    sf.write(path, np.asarray(audio), sr)


def chatterbox(path: Path, exaggeration: float, cfg: float, seed: int) -> bool:
    key = os.environ.get("DEEPINFRA_API_KEY")
    if not key:
        log("voice test: no DEEPINFRA_API_KEY")
        return False
    h = {"Authorization": f"Bearer {key}"}
    body = {"text": TEXT, "exaggeration": exaggeration, "cfg": cfg, "temperature": 0.8,
            "seed": seed, "response_format": "wav"}
    r = requests.post(f"https://api.deepinfra.com/v1/inference/{MODEL}", json=body, headers=h, timeout=300)
    log(f"chatterbox inference: HTTP {r.status_code} {r.headers.get('content-type')}")
    if r.ok and r.headers.get("content-type", "").startswith("audio"):
        path.write_bytes(r.content)
        return True
    if r.ok:
        data = r.json()
        audio = data.get("audio") or (data.get("output") or {}).get("audio") if isinstance(data, dict) else None
        if isinstance(audio, str):
            if audio.startswith("http"):
                path.write_bytes(requests.get(audio, timeout=120).content)
            else:
                path.write_bytes(base64.b64decode(audio.split(",", 1)[-1]))
            return True
        log(f"chatterbox: unexpected response keys {list(data)[:10]}")
    else:
        log(f"chatterbox error body: {r.text[:500]}")
    # OpenAI-compatible fallback
    r = requests.post("https://api.deepinfra.com/v1/openai/audio/speech", headers=h, timeout=300,
                      json={"model": MODEL, "input": TEXT, "response_format": "wav", "voice": "default",
                            "extra_body": {"exaggeration": exaggeration, "cfg": cfg}})
    log(f"chatterbox openai: HTTP {r.status_code} {r.headers.get('content-type')}")
    if r.ok and len(r.content) > 1000:
        path.write_bytes(r.content)
        return True
    log(f"chatterbox openai body: {r.text[:500]}")
    return False


def to_mp3(src: Path, dst: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-b:a", "160k", str(dst)], check=True)


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    raw = DEST / "raw"
    raw.mkdir(exist_ok=True)
    made: dict[str, Path] = {}
    p = raw / "kokoro.wav"
    kokoro(p)
    made["Kokoro bm_george (current)"] = p
    for name, ex, cfg in [("calm", 0.3, 0.5), ("expressive", 0.6, 0.4)]:
        p = raw / f"chatterbox-{name}.wav"
        if chatterbox(p, ex, cfg, 7):
            made[f"Chatterbox Turbo {name} (exaggeration {ex}, cfg {cfg})"] = p
    labels = list("ABCDEF")[:len(made)]
    random.shuffle(labels)
    key = {}
    for label, (name, src) in zip(labels, made.items()):
        to_mp3(src, DEST / f"{label}.mp3")
        key[label] = name
    (DEST / "key.json").write_text(json.dumps(dict(sorted(key.items())), indent=2))
    n_cb = len(made) - 1
    (DEST / "costs.json").write_text(json.dumps({"chatterbox_clips": n_cb,
        "usd_estimate": round(n_cb * len(TEXT) * USD_PER_CHAR, 5)}))
    log(f"voice test: {len(made)} clips, labels {sorted(key)}")


if __name__ == "__main__":
    main()
