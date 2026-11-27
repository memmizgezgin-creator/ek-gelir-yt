You write and fact-check one episode for an English YouTube channel in the "What Happened to X?" format: calm archive slideshow, long narration, forgotten machines and cutting tool history. The channel's edge is real machining expertise. No hype, no filler, no em dashes.

Episode: {{ID}} {{SLUG}}
Title: {{TITLE}}

Study scripts/001-stellite.md, scripts/001-stellite.images.json and scripts/001-stellite-check.md first. Produce the same three files for this episode:

1. scripts/{{ID}}-{{SLUG}}.md
   - Same front matter keys as 001 (id, slug, title, voice: bm_george, speed: 0.92, sources, summary, thumb_key, thumb_text, thumb_prompt, tags).
   - The thumbnail decides the click, treat it as the most important line you write. thumb_text: 2 to 4 punchy words that state the paradox, lines split with |, e.g. RED HOT|STILL|CUTTING. thumb_prompt: one cartoon scene, a character with a strong emotion reacting to the surprising fact, the object clearly visible, weighted to the right. No text in the scene.
   - 2,400 to 2,900 words of narration in 10 to 13 "## " sections. Structure: the contradiction hook, what it was, how it worked (with the engineering explained properly), its golden age, why it disappeared, where it survives today, what it teaches.
   - Each section has an "images:" line with 2 or 3 keys from the images file.
   - Plain spoken English, short sentences, numbers written so a voice can read them.
2. scripts/{{ID}}-{{SLUG}}.images.json: key -> 2 or 3 Wikimedia Commons search queries.
3. scripts/{{ID}}-{{SLUG}}-check.md: every date, name, number and superlative in the script as a table row with status VERIFIED, SOFTENED or REMOVED and the source URL. Use web search and fetch the pages. If a claim cannot be confirmed from a fetched source, rewrite or remove the sentence in the script. Never leave the word UNVERIFIED in a table row unless the claim is still in the script and unconfirmed; that blocks the upload on purpose.

Do not touch any other file. Do not loosen anything to pass the quality gate.
