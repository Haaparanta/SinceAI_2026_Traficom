# Demo video

The submission video (E5): the team's screen recording of [filingradar.click](https://filingradar.click), cut from
4:55 to 1:35, with a new English narration (ElevenLabs), burned-in captions, step labels, two zooms on the calculated
margins and a closing card in the Girlypop theme. Built with [Remotion](https://www.remotion.dev/) 4, which also
supplies the ffmpeg used here, so nothing else needs installing.

| File | What |
|---|---|
| [`narration_cut.json`](narration_cut.json) | The edit: per segment the source range of the recording (seconds), the spoken text and the on-screen caption. Every number matches what the screen shows at that moment. Also the voice settings |
| [`src/Cut.tsx`](src/Cut.tsx) | The composition: timing (each segment lasts as long as its narration; the recording plays up to 2.5x faster to fit, or holds its last frame), captions, labels, zooms, title and closing card |
| [`scripts/tts.mjs`](scripts/tts.mjs) | Narration: ElevenLabs with per-character timestamps when `ELEVENLABS_API_KEY` is set, otherwise the macOS `say` voice as a placeholder. Reuses audio whose text and voice have not changed |
| [`scripts/source.mjs`](scripts/source.mjs) | Crops and scales the raw recording to `public/source.mp4` |
| `public/audio_cut/`, `public/cut.timed.json` | The generated narration (committed, so the video renders without an API key) |
| `public/source.mp4`, `out/` | The recording proxy and the rendered video (git-ignored, too large) |

## Rebuild

```bash
cd video && npm install
node scripts/source.mjs "/path/to/2026-11-07 07-34-23.mp4"   # the screen recording, kept outside the repository
npm run voice                                                 # only after changing the narration or the voice
npm run render                                                # out/filing-radar-cut.mp4, about 5 minutes on an M1
npm run studio                                                # preview and scrub in the browser
```

The key goes in `video/.env` (git-ignored) as `ELEVENLABS_API_KEY=...`. The voice is ElevenLabs "Jessica"
(`cgSgspJ2msm6clMCkdW9`, young and upbeat); set `elevenlabs_voice_id` in `narration_cut.json` or `ELEVENLABS_VOICE_ID`
to try another, then `npm run voice` and `npm run render`.

## What the narration says, and where the numbers come from

| Segment | Claim | Source |
|---|---|---|
| overview | Space IFIC 3074: 199 notices screened, 135 flagged | `data/cache/space_3074.json` (`result.screened`, `result.flagged`), header of the screen |
| calc | CHINASAT-G over the RR Article 21 limit by 4.7 dB | finding F-3074-0005: result -107.13, limit -111.79, margin -4.66 dB(W/m2) in 1 MHz |
| terrestrial | Issue 3076: 4,057 notices, 65 flagged; Kostomuksha 13 dB over the T/R 25-08 trigger | `data/cache/terrestrial_3076.json`, finding F-3076-0001: 25.0 against 12 dB(uV/m) |
| letter | Filing Radar never sends anything | the letter banner on screen; no send function exists |

The recording shows the offline demo, so the explanation and letter on screen are the deterministic template, not
Claude; the narration does not claim otherwise.
