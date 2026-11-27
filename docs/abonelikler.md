# Subscriptions and paid services

Rule: no paid service beyond the Claude Max subscription. Remaining credits may be used. Every service that costs or could cost money is listed here.

| Service | Used for | Cost to this project | Status |
|---|---|---|---|
| Claude Max (existing) | Script writing and fact check in GitHub Actions via `CLAUDE_CODE_OAUTH_TOKEN` | Included in Max | Active once the token secret is set |
| GitHub (existing account) | Public repo, Actions runs, issues as failure alerts | Free: Actions minutes are unlimited on public repos | Production |
| Hetzner server (existing) | Not used: IPv6-only, cannot reach github.com; IPv4 would cost about 0.50 EUR/month | 0 | Off |
| Kokoro TTS | Narration | Free, open source (Apache-2.0), runs on the Actions runner | Active |
| Wikimedia Commons API | Images with license records | Free | Active |
| YouTube Data API v3 | Upload, thumbnail, captions | Free quota (10,000 units a day, one upload is about 1,600 + 50 + 400) | Needs one-time OAuth |
| Google Cloud project | Only to hold the OAuth client for YouTube | Free. No billing account needed for the YouTube Data API | Needs creation |
| Google Cloud TTS | Not used | Not used. Kokoro replaced it, so the 300 USD trial credit stays untouched | Off |
| fal.ai (4.83 USD left) | Not used | Thumbnails are made with Pillow, free | Off |
| Cloudflare Workers Paid (5 USD/month, existing) | Not used by this project (it runs the CuttingToolsAI workers) | Not charged to this project | n/a |
| Anthropic Console API credit | Not used | Removed from the plan: Console credit is separate pay-as-you-go API billing, not part of Max | Off |

Auto top-up and paid plans: none enabled anywhere. Do not enable.
