---
name: demo-video
description: Make an honest product demo video on a Mac: real terminal takes in Ghostty, site takes with agent-browser or Claude in Chrome, cues measured from the footage, captions and cards in the product's fonts, zoom keyframes, an ElevenLabs voice one line at a time, and checks before upload. Use when asked to make, record, redo or edit a demo or hackathon video, a product walkthrough, or a voiceover for one.
---

# Demo video

The kit lives in a repo (`demo-video-kit`). Find it from `.kit-path` next to this file, else at `~/Documents/Projects/mine/demo-video-kit`, else clone it. Read, in this order, before doing anything:

1. `docs/WORKFLOW.md` (the steps and the tools for each)
2. `docs/LEARNINGS.md` (what broke before and the fix)
3. `docs/PROMPTS.md` (narration rules)
4. `examples/ironclad/` (a real project: project.json, scenes.json, the take script)

Run `./install.sh` once on a new Mac and act on every "todo" it prints.

## The rules that matter most

- Every claim in the video has a real moment on screen. Never fake output; label any speed-up on screen.
- A voice line starts at its cue, the second its event appears in the footage. Measure cues with `kit/sheet.py --at ...` (exact seeks); never trust a 1/3 fps grid for timing.
- Clips start about a second before their first event and hold at least three seconds after their last output.
- Build silent and read `build/cues.png` from `kit/check.py` before spending money on voice. Every frame must show what its line says.
- One ElevenLabs file per line (`kit/tts.py`). The key is the `sk_` secret in the Keychain item `elevenlabs-api-key`; the user stores it in their own terminal.
- Run narration through the humanizer skill.
- The user watches the cut before anything is published, and publishes it themselves.

## Commands

```
kit/new.sh "<Name>" [theme]                       # project folder in ~/Movies
kit/term.sh --theme <t> -- ssh -t <host> screen -U -x demo
python3 -I kit/window-crop.py --color <terminal_bg>
kit/rec.sh raw/<take>.mp4 600 &                   # stop: touch /tmp/demo-rec-stop
python3 -I kit/sheet.py raw/<take>.mp4 /tmp/s.png --every 3 --crop <crop>
python3 -I kit/build.py <project> --stills
python3 -I kit/check.py <project>
python3 -I kit/tts.py <project> [line ids]
```

Report the result with the file paths, the length, the loudness, the overlap count and what the cue sheet showed.
