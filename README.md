# demo-video-kit

How Adil and Claude make honest product demo videos on a Mac: real terminal and site takes, cues measured from the footage, captions and cards in the product's own fonts, zoom keyframes, an ElevenLabs voice recorded one line at a time, and checks before anything is published. It made the Ironclad video (Free Society Hack, 4 Nov 2026) and carries what the Stockroom and Locate videos taught.

## Getting started

```
git clone git@github.com:adilhusain01/demo-video-kit.git ~/Documents/Projects/mine/demo-video-kit
cd ~/Documents/Projects/mine/demo-video-kit
./install.sh
```

install.sh checks ffmpeg, Ghostty, agent-browser and Node, installs the fonts, links the Claude Code skill to `~/.claude/skills/demo-video`, tests Screen Recording permission and looks for the ElevenLabs key. Store the key once, in your own terminal (it prompts for the `sk_` secret):

```
security add-generic-password -s elevenlabs-api-key -a "$USER" -w
```

Then, in Claude Code, ask for a video; the skill loads the workflow. Or by hand:

```
kit/new.sh "Product"                                   # ~/Movies/Product demo/
# record takes into raw/ (docs/WORKFLOW.md, steps 2 and 3), write scenes.json
python3 -I kit/build.py ~/Movies/"Product demo" --stills
python3 -I kit/check.py ~/Movies/"Product demo"
python3 -I kit/tts.py ~/Movies/"Product demo"
python3 -I kit/build.py ~/Movies/"Product demo"
```

## What's here

| Path | What |
|---|---|
| `kit/build.py` | Cuts the video from scenes.json: crops, speed-ups with labels, zoom keyframes, captions, cards, per-line voice, the .srt |
| `kit/tts.py` | ElevenLabs, one file per narration line, key from the Keychain |
| `kit/sheet.py` | Contact sheets of a take at exact times, for measuring cues |
| `kit/check.py` | Length, loudness, voice overlaps, and a frame for every line |
| `kit/rec.sh` | Screen recording until a stop file |
| `kit/term.sh` | A themed Ghostty window attached to a command (a take in screen on a server) |
| `kit/window-crop.py` | Finds a window's crop in the capture from its background colour |
| `kit/mouse-away.sh` | Parks the pointer out of shot |
| `kit/new.sh` | Starts a project folder |
| `kit/templates/take.sh` | The terminal take script pattern |
| `kit/frame.html`, `kit/themes/` | Cards and caption bands; Stockroom and Gruvbox themes |
| `skill/demo-video/SKILL.md` | The Claude Code skill |
| `skills-pack/humanizer` | The humanizer skill (MIT), for narration |
| `docs/` | WORKFLOW, LEARNINGS, PROMPTS, TOOLS |
| `examples/ironclad/` | The real Ironclad project: project.json, scenes.json, the take script |

## Requirements

macOS with Homebrew, Node 20 or newer, Python 3 (standard library only), Ghostty for terminal takes, and an ElevenLabs account. No API keys or recordings live in this repo; `.gitignore` keeps projects and secrets out.
