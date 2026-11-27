"""Topic queue. `next.py pick` prints id and slug of the next todo topic as
GitHub Actions outputs; `next.py done <id> <url>` marks it done (or "rendered" when there is no
YouTube url, so it is picked again once uploads work)."""
from __future__ import annotations

import os
import sys
from datetime import date

from common import TOPICS, load_json, save_json, fail


def main() -> None:
    data = load_json(TOPICS)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pick"
    if cmd == "pick":
        forced = os.environ.get("FORCE_ID", "").strip()
        # "rendered" = produced but never uploaded (YouTube not connected yet): redo it first
        pool = [t for t in data["topics"] if t["id"] == forced] if forced else (
            [t for t in data["topics"] if t["status"] == "rendered"]
            + [t for t in data["topics"] if t["status"] == "todo"])
        if not pool:
            fail("no todo topic left in topics.json")
        t = pool[0]
        lines = [f"id={t['id']}", f"slug={t['slug']}", f"title={t['title']}"]
        print("\n".join(lines))
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write("\n".join(lines) + "\n")
    elif cmd == "done":
        vid, url = sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""
        for t in data["topics"]:
            if t["id"] == vid:
                t.update(status="done" if url else "rendered", date=str(date.today()), url=url)
        save_json(TOPICS, data)
    else:
        fail(f"unknown command {cmd}")


if __name__ == "__main__":
    main()
