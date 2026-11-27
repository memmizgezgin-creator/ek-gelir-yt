# ek-gelir-yt

Faceless English YouTube channel, "What Happened to X?" format: calm archive slideshow, 15 to 20 minute narration, forgotten machines and cutting tool history. Fully automated, free tools only (see docs/abonelikler.md).

## Pipeline (GitHub Actions on a public repo, Mon/Wed/Fri 05:00 UTC)
1. `next.py pick`: next todo topic from topics.json (first 10 from group A, cutting tools)
2. Script + fact check: Claude (Max subscription) writes `scripts/NNN-slug.md`, `.images.json`, `-check.md` if missing (prompt: prompts/script-gen.md)
3. `images.py`: Wikimedia Commons, only PD / CC0 / CC BY / CC BY-SA, license record per image in `out/NNN/credits.txt`
4. `tts.py`: Kokoro narration, sentence by sentence, exact SRT captions
5. `render.py`: 1920x1080, slow zoom/pan, blurred fill, end card with sources and credits, soft subtitles
6. `thumbnail.py`: Pillow, 1280x720
7. `verify.py`: gate. Longer than 12 min, audio/video in sync, every image licensed, no UNVERIFIED claim. Upload runs only if it passes
8. `upload.py`: YouTube Data API, private until the API audit is approved (`YT_PRIVACY` variable)

Failures open a GitHub issue (GitHub emails the owner). `watchdog.yml` opens an issue if no video succeeded for 4 days, so a run that never started is not silent.

Manual run: Actions, produce, Run workflow (optional id, e.g. `001`). Alternative host: `server/` has a cron runner for any Linux box with IPv4 (`server/install.sh`).
One-time setup: docs/setup.md. API audit text: docs/youtube-audit.md.

Local run:
```
pip install -r requirements.txt && pipeline/get_models.sh
for s in images tts render thumbnail verify; do python3 pipeline/$s.py 001; done
```
