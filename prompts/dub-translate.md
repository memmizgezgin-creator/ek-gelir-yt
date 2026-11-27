Translate the narration of episode {{ID}} of an English documentary channel about cutting tool history into {{LANGUAGE}}, for a dubbed audio track that must line up with the original pictures.

Input: out/{{ID}}/sentences.txt (tab separated: index, start, length in seconds, section, English text).
Output: scripts/dub/{{ID}}.{{LANG}}.json as {"lang": "{{LANG}}", "lines": ["...", "..."]} with exactly one line per input row, in the same order. Never merge, split or skip rows; the count must match exactly.

Rules:
- Natural spoken {{LANGUAGE}} a native documentary narrator would use, not word for word.
- Each line must be speakable in about the same time as the English one. {{LANGUAGE}} runs longer than English, so keep lines tight: drop filler words, use short forms, keep it at or below the English character count where you can.
- Keep technical terms correct for machinists in that language (for example high-speed steel, cemented carbide, cobalt, tool bit, lathe). Keep names, alloy names and brand names as they are.
- Write numbers and years as words a speech engine reads correctly in {{LANGUAGE}}.
- No em dashes.

Write only that one file.
