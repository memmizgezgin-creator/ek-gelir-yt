# YouTube API Services audit: draft answers

Purpose: videos uploaded through `videos.insert` from an unverified API project (created after 28 July 2020) are locked to private. This audit lifts that restriction. Form: YouTube API Services, "Audit and Quota Extension Form" (support.google.com/youtube/contact/yt_api_form). Fill in the fields below. Replace the bracketed parts.

## Organization / applicant
- Name: [Murat Önder], individual developer, the Netherlands
- Contact email: [the Google account that owns the channel]
- Website / privacy policy URL: [a simple page, for example a GitHub Pages or Netlify page with the privacy text in the last section of this file]

## API client
- Google Cloud project name and number: ek-gelir-yt, [project number]
- OAuth client type: Desktop / installed application, used only by the owner
- APIs used: YouTube Data API v3
- Scopes: `youtube.upload`, `youtube.force-ssl` (caption upload only)

## Use case description (paste)
This is a private, single-user publishing tool for my own YouTube channel, [channel name and URL]. The channel publishes long-form English documentaries (15 to 20 minutes) about the history of machine tools, cutting tool materials and industrial engineering. I have worked in the cutting tools industry for many years and every episode is researched, fact-checked against cited sources and illustrated only with public domain or Creative Commons images from Wikimedia Commons, credited in the description.

The tool runs in my own GitHub repository on a schedule. It renders each finished episode with ffmpeg and calls the YouTube Data API to:
1. upload the video with `videos.insert` (title, description with sources and image credits, tags, category 27 Education, `containsSyntheticMedia: true` because narration is text-to-speech),
2. set the custom thumbnail with `thumbnails.set`,
3. upload the English caption track with `captions.insert`.

It only ever acts on my own channel, authorized once by me through OAuth. It has no other users, no user interface for third parties, stores no YouTube data, and does not read, download or analyze other channels' content. Expected volume: about 3 uploads a week, roughly 2,100 quota units per upload, well within the default 10,000 units a day. No quota increase is requested.

## Answers to common form questions
- Does your app serve other users? No, only the channel owner.
- Do you store YouTube API data? No. Only the uploaded video's ID is stored, in the repository, to link the episode.
- Do you display YouTube data to users? No.
- Do you use the data for advertising? No.
- Requested quota: default (10,000/day), no extension.
- Screencast: if asked, record the GitHub Actions run log plus the uploaded video in YouTube Studio.

## Compliance notes for the reviewer
- Policies: complies with the YouTube API Services Terms of Service and Developer Policies; the uploads follow YouTube's Community Guidelines and the altered or synthetic content disclosure.
- Content originality: each episode is an original script with cited sources, not reuploaded or compiled third-party video.
- Credentials: the refresh token is stored as an encrypted GitHub Actions secret, never in the repository.

## Privacy policy text (for the URL above)
ek-gelir-yt is a personal tool that uploads videos to the owner's own YouTube channel using the YouTube API Services. It is used only by its owner. It does not collect, store or share personal data of any other person. The OAuth token is kept in encrypted storage and used only to upload videos, thumbnails and captions to the owner's channel. Access can be revoked at any time at https://myaccount.google.com/permissions. By using YouTube features through this tool, the YouTube Terms of Service (https://www.youtube.com/t/terms) and the Google Privacy Policy (https://policies.google.com/privacy) apply.
