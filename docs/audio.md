# Audio standard (applies to every video)

Set in pipeline/shots.py, never adjusted per video.

| Item | Value | Why |
|---|---|---|
| Narration | normalised to -16 LUFS | consistent voice level between episodes |
| Music bed | normalised to the same scale, then 10 dB below the voice | common voice-over guidance puts music roughly 10 to 20 dB under speech; we sit at the audible end because Murat found -18 dB too quiet |
| Ducking | ratio 2.5, slow attack and release | music dips a further 3 to 4 dB while the narrator talks and comes back up in pauses, no pumping |
| Master | -14 LUFS integrated, true peak -1.5 dBTP | YouTube normalises playback to about -14 LUFS; delivering there means YouTube does not turn us down |
| Fades | 4 s in, 6 s out | no hard start or stop |

Music: calm CC BY 4.0 tracks by Kevin MacLeod (music/tracks.json), credit line added to every description.

References: YouTube loudness target and voice/music balance guidance from Descript, Sweetwater, Soundstripe and Storyblocks articles on audio levels for video.

## Voice
Blind test 2026-11-27 (samples/voice-test): Murat picked Kokoro bm_george over Chatterbox Turbo. Kokoro stays, free.
