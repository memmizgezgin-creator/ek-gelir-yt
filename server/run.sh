#!/usr/bin/env bash
# One production run on the server. Called by cron (Mon/Wed/Fri).
# Any failure opens a GitHub issue (GitHub emails the owner) and pings the
# dead-man switch with /fail. A run that never starts is caught by the
# dead-man switch (no ping for 4 days -> email).
set -uo pipefail
cd "$(dirname "$0")/.."
source server/.env            # GH_TOKEN, CLAUDE_CODE_OAUTH_TOKEN, YT_*, HC_URL (optional)
export CLAUDE_CODE_OAUTH_TOKEN YT_CLIENT_ID YT_CLIENT_SECRET YT_REFRESH_TOKEN YT_PRIVACY
REPO=memmizgezgin-creator/ek-gelir-yt
LOG="logs/run-$(date -u +%F-%H%M).log"
mkdir -p logs
exec > >(tee -a "$LOG") 2>&1

STEP=start
VID="?"
fail() {
  echo "FAILED at step: $STEP"
  body=$(printf 'Server run failed at step **%s** for video %s.\n\nLast log lines:\n```\n%s\n```\nGate report:\n```\n%s\n```' \
    "$STEP" "$VID" "$(tail -n 40 "$LOG")" "$(cat out/$VID/gate.json 2>/dev/null || echo none)")
  python3 - "$body" <<'PY'
import json, os, sys, urllib.request
req = urllib.request.Request(
    "https://api.github.com/repos/memmizgezgin-creator/ek-gelir-yt/issues",
    data=json.dumps({"title": "Pipeline failed on server", "body": sys.argv[1][:60000],
                     "labels": ["pipeline-failure"]}).encode(),
    headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}", "Accept": "application/vnd.github+json"})
urllib.request.urlopen(req, timeout=30)
PY
  [ -n "${HC_URL:-}" ] && curl -fsS -m 10 "$HC_URL/fail" >/dev/null || true
  exit 1
}
trap fail ERR
set -e

[ -n "${HC_URL:-}" ] && curl -fsS -m 10 "$HC_URL/start" >/dev/null || true

STEP=git-pull;   git pull --ff-only -q
STEP=venv;       source .venv/bin/activate
STEP=pick;       eval "$(python3 pipeline/next.py pick | sed 's/^/export /; s/=\(.*\)$/="\1"/')"; VID=$id
echo "video $id $slug"

if ! ls scripts/$id-*.md 2>/dev/null | grep -qv -- '-check.md'; then
  STEP=script-gen
  prompt=$(sed -e "s/{{ID}}/$id/g" -e "s/{{SLUG}}/$slug/g" -e "s|{{TITLE}}|$title|g" prompts/script-gen.md)
  claude -p "$prompt" --model sonnet --max-turns 60 \
    --allowedTools "Read,Write,Edit,Glob,Grep,WebSearch,WebFetch"
fi

for s in images tts render thumbnail verify; do STEP=$s; python3 pipeline/$s.py "$id"; done

URL=""
if [ -n "${YT_REFRESH_TOKEN:-}" ]; then
  STEP=upload; python3 pipeline/upload.py "$id"
  URL=$(python3 -c "import json;print(json.load(open('out/$id/upload.json'))['url'])")
else
  echo "YouTube not connected yet: video kept at out/$slug.mp4, not uploaded."
fi

STEP=commit
python3 pipeline/next.py done "$id" "$URL"
for f in topics.json scripts out/$id/credits.txt out/$id/credits.json out/$id/gate.json out/$id/*.srt out/$id/timeline.json out/$id/preview.jpg out/$id/thumbnail.jpg out/$id/upload.json; do [ -e "$f" ] && git add "$f"; done
git commit -qm "video $id $slug: produced" || true
git push -q

# keep disk small: drop render intermediates, keep the last 6 finished videos
rm -rf out/$id/frames out/$id/clips out/$id/narration.wav
ls -t out/*.mp4 2>/dev/null | tail -n +7 | xargs -r rm -f
find logs -name 'run-*.log' -mtime +60 -delete

[ -n "${HC_URL:-}" ] && curl -fsS -m 10 "$HC_URL" >/dev/null || true
echo "done: $id $URL"
