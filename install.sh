#!/bin/zsh
# Set up the demo video kit on a Mac. Safe to run twice; it only adds what is missing.
# Usage: ./install.sh            (installs, links the Claude skill, checks permissions)
set -u
KIT=${0:A:h}
ok() { printf '  \033[32mok\033[0m  %s\n' "$1"; }
todo() { printf '  \033[33mtodo\033[0m %s\n' "$1"; }

echo "Demo video kit: $KIT"

# Homebrew tools. ffmpeg does the cutting; Homebrew's build has zoompan, overlay and ebur128 but no
# drawtext or subtitles, which is why captions are rendered as images.
command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
for f in ffmpeg; do
  command -v $f >/dev/null && ok "$f $(ffmpeg -version | head -1 | cut -d' ' -f3)" || { brew install ffmpeg && ok "ffmpeg installed"; }
done
if [ -d /Applications/Ghostty.app ]; then ok "Ghostty (terminal takes)"; else
  todo "Ghostty is not installed. For terminal takes: brew install --cask ghostty"
fi

# Node, for agent-browser (site takes, card and caption rendering) and the fonts.
command -v node >/dev/null || { echo "Install Node 20 or newer first (nvm, Homebrew or nodejs.org)"; exit 1; }
if command -v agent-browser >/dev/null; then ok "agent-browser $(agent-browser --version | cut -d' ' -f2)"; else
  npm install -g agent-browser && agent-browser install && ok "agent-browser installed"
fi
(cd "$KIT" && npm install --no-audit --no-fund --silent) && ok "fonts in $KIT/node_modules"

# The Claude Code skill, linked so updates to this repo reach it.
mkdir -p "$HOME/.claude/skills"
if [ -L "$HOME/.claude/skills/demo-video" ] || [ -e "$HOME/.claude/skills/demo-video" ]; then ok "skill already at ~/.claude/skills/demo-video"; else
  ln -s "$KIT/skill/demo-video" "$HOME/.claude/skills/demo-video" && ok "skill linked: ~/.claude/skills/demo-video"
fi
# The skill finds the kit through this file.
echo "$KIT" > "$HOME/.claude/skills/demo-video/.kit-path" 2>/dev/null || true

# Screen Recording permission: one frame from the screen device.
dev=$(ffmpeg -hide_banner -f avfoundation -list_devices true -i "" 2>&1 | sed -n 's/.*\[\([0-9]*\)\] Capture screen 0.*/\1/p' | head -1)
if [ -n "$dev" ] && ffmpeg -hide_banner -loglevel error -y -f avfoundation -framerate 30 -pixel_format uyvy422 -i "$dev:none" -frames:v 1 /tmp/demo-kit-check.png 2>/dev/null; then
  ok "screen capture works ($(sips -g pixelWidth -g pixelHeight /tmp/demo-kit-check.png | awk '/pixel/{printf "%s ", $2}')pixels)"
  rm -f /tmp/demo-kit-check.png
else
  todo "Allow Screen Recording for your terminal app: System Settings, Privacy & Security, Screen & System Audio Recording"
fi

# ElevenLabs key, stored in the Keychain by you, never in a file.
if security find-generic-password -s elevenlabs-api-key >/dev/null 2>&1; then ok "ElevenLabs key in the Keychain"; else
  todo "Store your ElevenLabs secret key (starts with sk_) in your own terminal: security add-generic-password -s elevenlabs-api-key -a \"\$USER\" -w"
fi
echo "Done. Start a project with: $KIT/kit/new.sh \"Name\""
