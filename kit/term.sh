#!/bin/zsh
# Open a Ghostty window for a terminal take, in the theme's terminal colours, running <command>.
# Usage: kit/term.sh [--theme stockroom] [--font 19] [--cols 118] [--rows 31] -- <command...>
# Example (a take script running in a screen session on a server):
#   kit/term.sh -- ssh -t vps screen -U -x demo
#
# Learned on 2026-11-04:
# - `open -na Ghostty.app --args ... -e cmd` ignored the command and opened a login shell; --command= works.
# - The server had no terminfo for xterm-ghostty ("Cannot find terminfo entry"), so TERM=xterm-256color.
# - Start the remote screen session with `screen -U` and LANG=C.UTF-8, or every "…" shows as a broken glyph.
# - --wait-after-command keeps the window open if the command fails, so the error can be read.
# - --macos-titlebar-style=hidden drops the title bar; window-decoration=none did not on Ghostty 1.3.
set -eu
KIT=${0:A:h:h}
theme=stockroom font=19 cols=118 rows=31
while [ $# -gt 0 ] && [ "$1" != "--" ]; do
  case $1 in
    --theme) theme=$2; shift 2 ;;
    --font) font=$2; shift 2 ;;
    --cols) cols=$2; shift 2 ;;
    --rows) rows=$2; shift 2 ;;
    *) echo "unknown option $1"; exit 1 ;;
  esac
done
shift
[ $# -gt 0 ] || { echo "usage: kit/term.sh [options] -- <command...>"; exit 1; }
bg=$(python3 -I -c "import json,sys; print(json.load(open(sys.argv[1]))['terminal_bg'])" "$KIT/kit/themes/$theme.json")
fg=$(python3 -I -c "import json,sys; print(json.load(open(sys.argv[1]))['terminal_fg'])" "$KIT/kit/themes/$theme.json")
open -na Ghostty.app --args --font-size="$font" --window-width="$cols" --window-height="$rows" \
  --window-padding-x=36 --window-padding-y=28 --macos-titlebar-style=hidden \
  --window-position-x=100 --window-position-y=110 --background="$bg" --foreground="$fg" \
  --title=demo --wait-after-command=true \
  --command="/usr/bin/env TERM=xterm-256color LANG=en_US.UTF-8 $*"
sleep 4
osascript -e 'tell application "Ghostty" to activate'
"$KIT/kit/mouse-away.sh"
echo "Ghostty window open. Find its crop with: python3 -I $KIT/kit/window-crop.py --color $bg"
