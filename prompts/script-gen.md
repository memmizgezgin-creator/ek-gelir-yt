You write and fact-check one episode for an English YouTube documentary channel about forgotten machines and cutting tool history. The channel's edge is real machining expertise. No hype, no filler, no em dashes.

Episode: {{ID}} {{SLUG}}
Working title (topic only, rewrite it): {{TITLE}}

Study scripts/001-stellite.md, scripts/001-stellite.images.json and scripts/001-stellite-check.md for the file format only. Do not copy 001's structure. Read docs/learnings.md and docs/script-structures.md, and check the "skeleton:" line in the front matter of every existing scripts/*.md so this episode uses a different skeleton from the last two episodes.

Produce the same three files for this episode:

1. scripts/{{ID}}-{{SLUG}}.md
   - Same front matter keys as 001 (id, slug, title, voice: bm_george, speed: 0.92, sources, summary, thumb_key, thumb_text, thumb_prompt, tags), plus skeleton: <name from docs/script-structures.md>, thumb_text_2, thumb_prompt_2, thumb_text_3, thumb_prompt_3.
   - title: built around the big consequence, with the tool or alloy as the subject. Pattern: "The <thing> That <consequence>" or "How <thing> <consequence>", optionally ending in ": <name>". Example: "The Steel That Made Machine Guns Possible". Under 70 characters. It must be true and backed by the check file. Never start with "What Happened to".
   - Three thumbnails for YouTube Test & Compare, each a different idea, not the same scene with another seed: (1) the paradox (thumb_text, thumb_prompt), (2) the consequence or scale, e.g. the war, the factory, the record (thumb_text_2, thumb_prompt_2), (3) the person or the rival (thumb_text_3, thumb_prompt_3). thumb_text*: 2 to 4 punchy words, lines split with |. thumb_prompt*: one cartoon scene, a character with a strong emotion reacting to the surprising fact, the object clearly visible, weighted to the right, no text in the scene.
   - 2,400 to 2,900 words of narration in 10 to 13 "## " sections, following the chosen skeleton.
   - Rules for every skeleton:
     - The first 15 seconds (about 40 words) open on the hardest, most dramatic moment of the story. No channel intro, no "in this video", no greeting. Then say plainly what was at stake.
     - Open a question early and keep at least one open loop alive every 2 to 3 minutes (about every 350 to 450 words): tease something you pay off later, and pay off every loop you open.
     - There is a clear villain or constraint: a rival material, a patent fight, a war deadline, physics itself. Name it and let it push the story.
     - One section near the end, "## Where you see it today", in the voice of a machining specialist: where this tool or idea still works on the shop floor today, with concrete applications, cutting speeds or materials. This is the channel's own perspective; make it specific, not generic.
     - AI illustrations are reconstructions, not footage; never describe them as photos.
   - Each section has an "images:" line with 2 or 3 keys from the images file.
   - Plain spoken English, short sentences, numbers written so a voice can read them.
2. scripts/{{ID}}-{{SLUG}}.images.json: key -> 3 or 4 Wikimedia Commons search queries. Ask for period interiors, people at work, machines and patent drawings, not building exteriors.
3. scripts/{{ID}}-{{SLUG}}-check.md: every date, name, number and superlative in the script (including the title) as a table row with status VERIFIED, SOFTENED or REMOVED and the source URL. Use web search and fetch the pages. If a claim cannot be confirmed from a fetched source, rewrite or remove the sentence in the script. Never leave the word UNVERIFIED in a table row unless the claim is still in the script and unconfirmed; that blocks the upload on purpose.

Do not touch any other file. Do not loosen anything to pass the quality gate.
