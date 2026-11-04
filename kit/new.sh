#!/bin/zsh
# Start a video project: ~/Movies/<Name> demo/ with project.json, scenes.json and the folders build.py uses.
# Usage: kit/new.sh "<Name>" [theme=stockroom]
set -eu
KIT=${0:A:h:h}
name=$1; theme=${2:-stockroom}
slug=$(echo "$name" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')
dir="$HOME/Movies/$name demo"
[ -e "$dir/project.json" ] && { echo "$dir already has a project"; exit 1; }
mkdir -p "$dir"/{raw,assets/vo,assets/caps,build}
cat > "$dir/project.json" <<EOF
{
  "name": "$slug-demo",
  "theme": "$theme",
  "crop": null,
  "band": 120,
  "voice": { "id": "EXAVITQu4vr4xnSDxMaL", "model": "eleven_multilingual_v2" },
  "cards": {
    "title": { "headline": "$name: what it does, in one line.", "sub": "Recorded live, $(date '+%-d %B %Y')." },
    "end": { "headline": "$name", "lines": ["github.com/you/$slug"], "sub": "Where it was built, and the licence." }
  }
}
EOF
cat > "$dir/scenes.json" <<'EOF'
{
  "scenes": [
    { "id": "title", "card": "title", "seconds": 3.0, "lines": [] },
    { "id": "first", "src": "raw/terminal.mp4", "crop": true, "in": 5.0, "out": 20.0, "lines": [
      { "at": 0.5, "text": "Say what the viewer is about to see." },
      { "at": 7.0, "text": "Say what just happened, once it is on screen." } ] },
    { "id": "end", "card": "end", "seconds": 5.0, "lines": [
      { "at": 0.4, "text": "Where to get it. Thanks for watching." } ] }
  ]
}
EOF
echo "$dir"
echo "Next: record takes into raw/, measure cues with kit/sheet.py, then: python3 -I $KIT/kit/build.py \"$dir\" --stills"
