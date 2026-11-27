# ek-gelir-yt

Faceless English YouTube channel, "What Happened to X?" format: calm archive slideshow, 15 to 20 minute narration, forgotten machines and cutting tool history. Fully automated, free tools only (see docs/abonelikler.md).

## Pipeline (Hetzner server cron, Mon/Wed/Fri 05:00 UTC; `server/run.sh`)
1. `next.py pick`: next todo topic from topics.json (first 10 from group A, cutting tools)
2. Script + fact check: Claude (Max subscription) writes `scripts/NNN-slug.md`, `.images.json`, `-check.md` if missing (prompt: prompts/script-gen.md)
3. `images.py`: Wikimedia Commons, only PD / CC0 / CC BY / CC BY-SA, license record per image in `out/NNN/credits.txt`
4. `tts.py`: Kokoro narration, sentence by sentence, exact SRT captions
5. `render.py`: 1920x1080, slow zoom/pan, blurred fill, end card with sources and credits, soft subtitles
6. `thumbnail.py`: Pillow, 1280x720
7. `verify.py`: gate. Longer than 12 min, audio/video in sync, every image licensed, no UNVERIFIED claim. Upload runs only if it passes
8. `upload.py`: YouTube Data API, private until the API audit is approved (`YT_PRIVACY` variable)

Failures open a GitHub issue (GitHub emails the owner). A healthchecks.io dead-man switch emails if no run succeeds for 4 days, so a run that never starts (server down, cron broken) is not silent.

Server install: `server/install.sh`, then fill `server/.env` from `server/env.example`. Manual run: `server/run.sh` (set `FORCE_ID=001` to rebuild one video). `.github/workflows/produce.yml` is a manual-only fallback.
One-time setup: docs/setup.md. API audit text: docs/youtube-audit.md.

Local run:
```
pip install -r requirements.txt && pipeline/get_models.sh
for s in images tts render thumbnail verify; do python3 pipeline/$s.py 001; done
```
