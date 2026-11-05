# Learnings

Everything that went wrong or took time across the Locate (7 Oct 2026), Stockroom (11 Oct 2026) and Ironclad (4 Nov 2026) videos, with the fix. Read this before recording.

## Honesty, which is the whole point

- Every claim in the narration has a moment on screen. If a step can't be shown for real, say less, not more.
- Never fake output. A sped-up wait is fine with a visible label ("Waiting for the block, 8x speed"); a cut that hides a failure is not.
- Say test things are test things: "Bitrefill's test top-up through the live API", not "a phone top-up".
- If a public explorer can't show a transaction, prove it another way on camera (Ironclad used `zcash-devtool inspect --lookup <txid>` against the same server the judges use).

## Timing and cuts

- A voice line starts when its event is on screen. Write each line's cue (`at`) from the footage, not from the script.
- Measure cues with exact seeks (`kit/sheet.py --at ...`). ffmpeg's `fps=1/3` grid picks frames from the middle of each interval, so its frame N is about (N-1)*3 + 1.5 seconds, not (N-1)*3. Ironclad's first upload opened a scene on an idle screen for 2.3 s because a clip start came from such a grid.
- Pixel-count tricks for finding events fail: a blinking cursor flips the counts every half second. Look at the frames.
- Give every clip a lead-in of about a second and a hold of at least three seconds after its last output. When a line runs long, hold the last frame (build.py does) instead of cutting mid-event.
- One voice file per line (not per scene) lets each line start on its own cue and lets you regenerate one line without retiming the rest.
- Check the finished cut with `kit/check.py`: the cue sheet shows a frame from half a second into every line. This is how the idle-screen flaw was found.
- Keep it under 3 minutes for hackathons; judges watch the first 3. Ironclad landed at 2:49.

## Terminal takes

- Run the take as a script inside `screen` on the server and attach a Ghostty window on the Mac. The script waits for a go file, so the recorder starts first and nothing is missed.
- `screen -U` and `LANG=C.UTF-8`, or "…" and other non-ASCII characters print as a broken glyph. The first Ironclad take had to be partly redone for this.
- Ghostty: `--command="..."` works where `-e` was ignored; set `TERM=xterm-256color` in the command because servers lack the `xterm-ghostty` terminfo; `--macos-titlebar-style=hidden` hides the title bar; `--wait-after-command=true` keeps a failed window open so you can read the error.
- Tools that open `/dev/tty` (zcash-devtool) fail with "Resource temporarily unavailable (os error 11)" under nohup or setsid. Screen gives them a terminal; `script -qec "<cmd>" /dev/null` does too.
- Park the pointer (`kit/mouse-away.sh`): the capture hides the cursor, but the I-beam over a terminal can still show.
- Stage Manager hides windows that aren't in front; activate Ghostty before recording.
- Split takes into parts so an expensive step (a real purchase under a daily cap) is recorded once. Bitrefill allows 5 phone top-ups a day per account; the Ironclad video used the 4th.
- Before a take that drives a live system, check for stray background processes. A second co-signer daemon on the same session folder made every Ironclad run fail with "request from another session" until it was found. `pgrep -f <pattern>` matches your own shell command line too, so `pkill -f` on a pattern you just typed can kill the command itself.

## Screen capture

- `ffmpeg -f avfoundation -i "<n>:none"`, where n is the index of "Capture screen 0". The index moves when cameras (OBS Virtual Camera, Desk View) come and go; look it up by name every time (rec.sh does).
- The capture is in backing pixels: 3600x2338 on a 14-inch MacBook Pro at "More Space", not the 3024x1964 the display reports and not the point coordinates windows use. Find crops from a frame (`kit/window-crop.py`), never from window positions.
- Keep raw takes uncropped; crop in the edit. A wrong crop then costs a rebuild, not a retake.
- The terminal running Claude Code needs Screen Recording permission. The first capture of a session can show private windows: delete test frames you don't need.

## Browser takes

- agent-browser's `record start` records just the page at the viewport you set, with an optional synthetic cursor. Best for public pages.
- Claude in Chrome drives the user's real Chrome with their sign-ins. It can't see tabs the user opened before; it opens its own tab group. While its debugger is attached Chrome shows an infobar about 112 px tall at the top of the page; crop it out.
- Claude in Chrome will not approve on-chain transactions on a deployed site, even for a burner wallet; the user clicks the wallet prompt (Locate). Plan the take around that.
- Headless YouTube embeds render black in screenshots; check them in a real browser.

## Captions and cards

- Homebrew's ffmpeg has no `drawtext` or `subtitles` filter (no freetype or libass). Captions and cards are rendered as PNGs from HTML in a headless browser and overlaid; this also means the product's own fonts are used.
- Put captions in a band under the footage (120 px), not over it: terminal text runs to the bottom of the frame.
- Ship an .srt too; YouTube takes it as captions.

## Voice (ElevenLabs)

- Each key has two values. The 64-character one is the key ID and is refused with `api_key_id_used_as_api_key`. The secret starts with `sk_`, is about 51 characters, and is shown once when the key is created. tts.py checks the prefix before calling.
- Store it in the Keychain from your own terminal, not through Claude's `!` prompt, so it never enters a transcript: `security add-generic-password -s elevenlabs-api-key -a "$USER" -w`. Replacing needs `-U`, or delete first; check that the item's modification date changed.
- The free plan refuses library voices over the API. Premade voices work; Sarah (`EXAVITQu4vr4xnSDxMaL`) with `eleven_multilingual_v2`, stability 0.55, similarity 0.75.
- Pass `previous_text` and `next_text` with each line so the delivery flows across separate files.
- The mix landed at -16.6 LUFS integrated with a -0.9 dB peak without any normalising, which is fine for YouTube.

## Working with Claude Code's safety checks

These were refused in auto mode, rightly, and are the user's to do:
- Posting to someone else's GitHub repo (an issue on an upstream project): give the user the exact `gh` command.
- Reading or searching for credentials (dumping the Keychain, grepping env files for keys): ask the user to store the key under a known name instead.
- Cloning and compiling unknown external repos, typing into another program's terminal.
- Publishing (YouTube, a submission form, a forum post): the user does it, or says yes to it first.

## Hosting the demo site

- Public demo sites go on Vercel or a subdomain of Adil's domain, on port 443 (his rule, 5 Nov 2026). A Tailscale Funnel address on port 8443 would not open on the organisers' laptop on the venue Wi-Fi at the Free Society demo day, and the live demo was lost. Check the link from a phone on mobile data before any event.
- If the product's server serves the site from its own address, the page and its API share one origin and no CORS is needed; the judges' URL never changes.
- A dashboard that runs a long job per click should start it in the background and stream lines through a state endpoint the page polls, instead of holding the request open for a minute.
- Serve video with HEAD and byte-range support, or Safari and iPhones won't play it.
