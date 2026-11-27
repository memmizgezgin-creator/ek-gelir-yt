# Subscriptions and paid services

Rule: no paid service beyond the Claude Max subscription. Remaining credits may be used. Every service that costs or could cost money is listed here.

| Service | Used for | Cost to this project | Status |
|---|---|---|---|
| Claude Max (existing) | Script writing and fact check in GitHub Actions via `CLAUDE_CODE_OAUTH_TOKEN` | Included in Max | Active once the token secret is set |
| Hetzner server (existing) | Runs the pipeline by cron: images, TTS, render, upload | Already paid for other work, no extra cost if there is room (2 vCPU, 2 GB RAM, about 3 GB disk) | Production |
| GitHub (existing account) | Private repo, issues as failure alerts | Free. Actions not used (account billing lock on private repos) | Active |
| healthchecks.io | Dead-man switch: email if no successful run for 4 days | Free plan (20 checks) | Needs one-time signup |
| Kokoro TTS | Narration | Free, open source (Apache-2.0), runs on the Actions runner | Active |
| Wikimedia Commons API | Images with license records | Free | Active |
| YouTube Data API v3 | Upload, thumbnail, captions | Free quota (10,000 units a day, one upload is about 1,600 + 50 + 400) | Needs one-time OAuth |
| Google Cloud project | Only to hold the OAuth client for YouTube | Free. No billing account needed for the YouTube Data API | Needs creation |
| Google Cloud TTS | Not used | Not used. Kokoro replaced it, so the 300 USD trial credit stays untouched | Off |
| fal.ai (4.83 USD left) | Not used | Thumbnails are made with Pillow, free | Off |
| Cloudflare Workers Paid (5 USD/month, existing) | Not used by this project (it runs the CuttingToolsAI workers) | Not charged to this project | n/a |
| Anthropic Console API credit | Not used | Removed from the plan: Console credit is separate pay-as-you-go API billing, not part of Max | Off |

Auto top-up and paid plans: none enabled anywhere. Do not enable.
