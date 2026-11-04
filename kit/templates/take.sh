#!/usr/bin/env bash
# A terminal take: real commands, typed on screen, with captions as "# ..." lines between them.
# Copy it into the product's repo (docs/video-run.sh), replace the scenes, and run it inside a screen
# session so a Ghostty window on the Mac can attach before it starts:
#
#   on the server:  LANG=C.UTF-8 screen -U -dmS demo bash docs/video-run.sh [part]
#   on the Mac:     kit/term.sh -- ssh -t <host> screen -U -x demo
#                   kit/rec.sh raw/terminal.mp4 &     then: ssh <host> touch /tmp/demo-go
#   it ends with:   /tmp/demo-done on the server; touch /tmp/demo-rec-stop on the Mac to stop recording.
#
# Rules that keep a take usable:
# - Every command is real. Never print a fake result; if something must wait (a block, a webhook), wait
#   for it in the script and speed it up in the edit with a visible label.
# - Parts ("all", "attacks", ...) let you re-record one stretch without redoing an expensive one
#   (a real purchase, a capped API call).
# - sleep after each output, so the edit has a hold of at least three seconds after the last line.
# - UTF-8: export LANG/LC_ALL and start screen with -U, or "…" and other characters break.
# - Tools that open /dev/tty (zcash-devtool did) fail without a terminal; screen gives them one.
set -u
PART=${1:-all}
export LANG=C.UTF-8 LC_ALL=C.UTF-8

say() { printf '\n\033[38;5;208m# %s\033[0m\n' "$1"; sleep "${2:-1.5}"; }
typed() { # print the command as if typed, then run it for real
  printf '\033[38;5;250m$ \033[0m'
  local text="$*" i
  for ((i = 0; i < ${#text}; i++)); do printf '%s' "${text:i:1}"; sleep 0.025; done
  printf '\n'; sleep 0.3
  eval "$text"
}

rm -f /tmp/demo-go /tmp/demo-done
clear
printf '\033[38;5;250mwaiting for the recorder...\033[0m'
while [ ! -f /tmp/demo-go ]; do sleep 0.2; done
clear

if [ "$PART" = all ]; then
  say "What this shows, in one line." 2.5
  typed "echo replace me with the first real command"
  sleep 3
fi

say "The next part." 2
typed "echo replace me"
sleep 3

printf '\n\033[38;5;250mdone\033[0m\n'
touch /tmp/demo-done
sleep 600
