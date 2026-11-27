Find public domain patent drawings on Wikimedia Commons for print-on-demand posters for the YouTube channel Lost Tool Archive (history of cutting tools and machine tools).

Use the Commons API (https://commons.wikimedia.org/w/api.php, e.g. action=query&list=search&srnamespace=6&srsearch=...) and check each file page. Look for drawings of: twist drills, lathes, milling machines, shapers, planers, tool holders and tool posts, taps and dies, files, saws, gear cutters, turret lathes, screw machines. Patent drawings from the US, UK, German or French patent offices before about 1925 are usually public domain.

Pick 8 files that:
- are the actual patent drawing sheet (black line art), not a photo, not a text page,
- are at least 2000 pixels on the long side,
- carry a public domain license on Commons (not CC BY or CC BY-SA),
- show one clear machine or tool that looks good framed on a wall.

Write posters/list.json as a JSON array of 8 objects:
{"file": "File:<exact Commons title>", "title": "<2 to 4 words, e.g. Twist Drill>", "subtitle": "<inventor> · <US Patent No. 38,119> · <year>"}
Only state the inventor, number and year if the file page says so; otherwise use what it does say. No em dashes.

Write only that file.
