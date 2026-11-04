# Workflow: from a working product to a published demo video

This is the order that worked for the Ironclad, Stockroom and Locate videos. Each step says what to do, which kit tool does it, and how to know it worked. A typical run takes about two hours: half recording, half cutting.

## 0. Before anything

- Run `./install.sh` once per Mac. It checks ffmpeg, Ghostty, agent-browser, the fonts, Screen Recording permission and the ElevenLabs key, and links the skill.
- Decide what the video must prove. Write the claims down first, one per line ("the agent's purchase is co-signed and delivered", "a payment over the cap is refused at the key"). Every claim needs a real moment on screen. If you can't show it, cut the claim.
- Check the judging rules if it is for a hackathon: length (judges often watch only the first 3 minutes), required moments (a real purchase on camera, a txid), anything that must not be mocked.

## 1. Plan the shots

- One shot per claim: a terminal take for anything that runs in a shell, a site take for anything in a browser, a still or a short take for an explorer or a dashboard.
- Order: title card, what it is (site hero), how it works, the happy path, the attacks or edge cases, the proof (chain, logs), the end card.
- Expensive or capped actions (real purchases, rate-limited APIs) get their own part of the take script, so a retake of another part never costs one again.

## 2. Terminal takes

1. Write the take script from `kit/templates/take.sh` into the product's repo (`docs/video-run.sh`). Captions are `# ...` lines printed in orange between commands; commands are printed as typed and then run for real.
2. Start it in a UTF-8 screen session on the machine that runs the product:
   ```
   LANG=C.UTF-8 screen -U -dmS demo bash docs/video-run.sh all
   ```
3. On the Mac, open the window and park the pointer:
   ```
   kit/term.sh --theme stockroom -- ssh -t <host> screen -U -x demo
   ```
4. Find the window's crop once (it is stable while the window doesn't move) and put it in `project.json` as `"crop"`:
   ```
   python3 -I kit/window-crop.py --color <terminal_bg from the theme>
   ```
5. Record, start the take, stop when it is done:
   ```
   kit/rec.sh raw/terminal.mp4 600 &
   ssh <host> touch /tmp/demo-go
   # wait for /tmp/demo-done on the host, then:
   touch /tmp/demo-rec-stop
   ```
6. Look at the last frame before moving on (`kit/sheet.py raw/terminal.mp4 /tmp/end.png --at <duration-2> --crop <crop>`). Broken characters, a wrong command or a failed run means a retake now, not later.

## 3. Site takes

Use agent-browser's own recorder for pages: it records the page at an exact viewport (1920x1080), with an optional animated cursor, and no desktop around it.
```
export AGENT_BROWSER_SESSION=demo-site
agent-browser set viewport 1920 1080
agent-browser open https://your.site
agent-browser record start raw/site.mp4 --cursor
agent-browser wait 4500
agent-browser scroll down 820
agent-browser find text "Step two" click
agent-browser record stop
```
Waits between actions are the holds in the edit: 4 to 5 seconds per thing the viewer must read. For a page that needs the user's own sign-in or a wallet extension, use Claude in Chrome in the user's real browser instead, and record the screen with `kit/rec.sh` (see LEARNINGS.md for the infobar it adds).

## 4. Find the cues

A cue is the second, inside a take, when an event appears on screen. The voice line about that event starts at its cue, never before.

1. Rough pass, a frame every 3 seconds: `python3 -I kit/sheet.py raw/terminal.mp4 /tmp/s.png --every 3 --crop <crop>`
2. Fine pass inside each window, every half second: `--at 24.5,25,25.5,26,26.5,27`
3. Read the sheets as images and write the times into `scenes.json`.

Measure the start of every clip as carefully as the events: the first Ironclad upload opened its attacks scene on an idle "waiting for the recorder" screen for 2.3 seconds because the start came from a rough grid.

## 5. Write the cut

`scenes.json` holds one entry per scene:

```json
{ "id": "buy", "src": "raw/terminal.mp4", "crop": true, "in": 19.5, "out": 45.0,
  "zoom": [[0, 1, 0.5, 0.5], [16, 1, 0.5, 0.5], [17, 1.6, 0.3, 0.8], [24, 1.6, 0.3, 0.8]],
  "lines": [
    { "at": 0.5, "text": "Now the agent buys a phone top-up." },
    { "at": 18.0, "text": "Then it asks the co-signer, which checks the payment itself against the rules." } ] }
```

- `in`, `out`: seconds in the take. Start about a second before the first event; end at least three seconds after the last output.
- `crop`: `true` uses the project's crop, a string `w:h:x:y` overrides it, absent means the take is already framed (site takes).
- `speed`: for waits only (a block being mined), with a `label` that says so on screen ("Waiting for the block, 8x speed").
- `zoom`: keyframes `[seconds into the clip, scale, focus x, focus y]`, focus as a fraction of the frame. Zoom in on the line that matters (a refusal, a txid), hold, zoom out. Keep it to one or two zooms per scene; every zoom must point at something the voice is saying.
- `lines`: `at` is the cue in seconds into the clip. Lines queue: one that would overlap the line before waits for it.
- Cards: `{ "id": "title", "card": "title", "seconds": 3.0, "lines": [] }`, with the text in `project.json` under `cards`.

## 6. Narration

Rules in PROMPTS.md. One line per event, written to be heard: short sentences, the product's real names, no claim the footage doesn't show. Run every line through the humanizer skill.

## 7. Build silent, check, then voice

```
python3 -I kit/build.py <project> --stills     # renders cards and captions, estimates line lengths
python3 -I kit/check.py <project>              # writes build/cues.png
```
Read `build/cues.png`: every frame must show what its line says. Fix cues, rebuild, repeat. Only then make the voice, which costs money:
```
python3 -I kit/tts.py <project>                # every line, one file each
python3 -I kit/tts.py <project> buy-2 chain-1  # only the lines you changed
python3 -I kit/build.py <project>
python3 -I kit/check.py <project>
```
`check.py` must report 0 overlapping lines and loudness near -16 LUFS with the peak below -1 dB.

## 8. Hand over

- The user watches it. Publishing (YouTube, a submission form) is theirs: never upload from an account that isn't theirs, and never publish without their yes.
- Upload `<name>.mp4` and `<name>.srt` (the captions file) to YouTube as unlisted unless they say otherwise. Put the link in the README and the submission.
- Keep `raw/` and the previous cut (`raw/<name>-v1.mp4`) until the deadline has passed.
