# Tools, versions and permissions

Versions are the ones the Ironclad video was made with on 4 Nov 2026.

| Tool | Version | What it does here | Install |
|---|---|---|---|
| macOS | 27.0.1 | avfoundation screen capture, Keychain, osascript | |
| ffmpeg | 9.0.1 (Homebrew) | capture, crop, speed, zoompan, overlays, concat, mix, loudness | `brew install ffmpeg` |
| Ghostty | 1.3.1 | the terminal window for terminal takes | `brew install --cask ghostty` |
| agent-browser | 0.38.1 | site takes (`record start`), rendering cards and captions | `npm i -g agent-browser && agent-browser install` |
| Node | 26.7 | agent-browser, the fonts | nvm or Homebrew |
| Python | 3.14 (standard library only) | build, tts, sheet, check, window-crop | comes with Homebrew |
| GNU screen | on the server | holds the take so the Mac can attach | `apt install screen` |
| ElevenLabs | API v1, `eleven_multilingual_v2` | the voice, one file per line | key in the Keychain |
| Fonts | @fontsource-variable packages | the product's type on cards and captions | `npm install` in the kit (install.sh) |

## Claude capabilities

- **Claude Code** in a terminal on the Mac that records. Auto mode works; see LEARNINGS.md for what it refuses.
- **Claude in Chrome** (the browser extension) for takes that need the user's real browser and sign-ins. Install the extension from the Chrome Web Store and connect it in Claude; in Claude Code the tools are `mcp__claude-in-chrome__*` and load with one ToolSearch call.
- **Computer use** is an alternative for driving native apps; terminal takes here use a script in screen instead, which is repeatable and needs no clicking.

## Skills

| Skill | Use | Where |
|---|---|---|
| demo-video | this kit's workflow | `skill/demo-video`, linked by install.sh |
| humanizer | every narration line, card and caption | copied in `skills-pack/humanizer` (MIT, blader/humanizer); install with `cp -R skills-pack/humanizer ~/.claude/skills/` or `npx skills add blader/humanizer` |
| agent-browser | browser automation guide | `npx skills add vercel-labs/agent-browser` (a stub that serves `agent-browser skills get core`) |
| claude-in-chrome | the Chrome extension's rules | built into Claude Code when the extension is connected |
| hyperframes family | an alternative editor (HTML compositions, GSAP keyframes) used for Stockroom and Locate | HeyGen's HyperFrames skills; this kit does the same jobs with ffmpeg alone |

## Permissions on a new Mac

1. Screen Recording for the terminal app Claude Code runs in (System Settings, Privacy & Security, Screen & System Audio Recording). install.sh tests it.
2. Accessibility is not needed: the pointer is moved with CoreGraphics and windows are activated with osascript.
3. SSH access to the server that runs the product, from the same Mac.
