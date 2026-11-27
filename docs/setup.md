# One-time setup (Murat)

Everything else runs by itself. These are the only manual steps, each done once.

## 1. YouTube channel
Create the channel on the Google account that will own it. Suggested name: "Lost Tool Archive" or similar, not a copy of an existing channel name. Verify the channel with a phone number (needed for videos over 15 minutes and for custom thumbnails).

## 2. Google Cloud OAuth client (free, no billing)
1. console.cloud.google.com, create project `ek-gelir-yt`.
2. APIs and Services, Library, enable "YouTube Data API v3".
3. OAuth consent screen: External, app name `ek-gelir-yt`, your email as support and developer contact. Scope: `https://www.googleapis.com/auth/youtube.upload` and `https://www.googleapis.com/auth/youtube.force-ssl` (captions). Add yourself as a test user, then press "Publish app" so the refresh token does not expire after 7 days.
4. Credentials, Create OAuth client ID, type "Desktop app". Copy client ID and secret.

## 3. Refresh token (one command on the Mac)
```
python3 pipeline/oauth_once.py <CLIENT_ID> <CLIENT_SECRET>
```
A browser opens, pick the channel, allow. The script prints the refresh token.

## 4. Server secrets (server/.env on the Hetzner box, chmod 600)
Same values as below go in `server/.env` (template: `server/env.example`). Add `GH_TOKEN`: a fine-grained GitHub token for this repo only, Contents read/write and Issues read/write. Add `HC_URL`: create a free check on healthchecks.io with period 3 days, grace 1 day, and paste its ping URL.

The list below is the same set as GitHub Actions secrets, only needed if the manual Actions fallback is used.

## 4b. GitHub secrets (optional fallback)
- `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` from steps 2 and 3
- `CLAUDE_CODE_OAUTH_TOKEN`: run `claude setup-token` on the Mac (uses the Max subscription)
- Variable `YT_PRIVACY` = `private` until the API audit is approved, then `public`
- Optional: `MAIL_USERNAME` + `MAIL_APP_PASSWORD` (Gmail app password) for a second failure email. Without them, failures still arrive by email as GitHub issue notifications.

## 5. API audit
Submit the text in docs/youtube-audit.md through the YouTube API Services audit form. Until it is approved, uploads stay private.
