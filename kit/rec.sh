#!/bin/zsh
# Record the whole main screen to <out.mp4> until <stop-file> appears or <max-seconds> pass.
# Usage: kit/rec.sh <out.mp4> [max-seconds=600] [stop-file=/tmp/demo-rec-stop]
# The raw take is never cropped; build.py crops it later from scenes.json, so a bad crop never costs a retake.
# Needs Screen Recording permission for the app that runs this (the terminal Claude Code runs in).
set -eu
out=$1; max=${2:-600}; stop=${3:-/tmp/demo-rec-stop}
rm -f "$stop"
# The screen's avfoundation index changes when cameras come and go; look it up by name.
dev=$(ffmpeg -hide_banner -f avfoundation -list_devices true -i "" 2>&1 | sed -n 's/.*\[\([0-9]*\)\] Capture screen 0.*/\1/p' | head -1)
[ -n "$dev" ] || { echo "no 'Capture screen 0' device; is Screen Recording allowed?"; exit 1; }
ffmpeg -hide_banner -loglevel error -y -f avfoundation -framerate 30 -capture_cursor 0 -pixel_format uyvy422 -i "$dev:none" -t "$max" \
  -r 30 -c:v libx264 -preset veryfast -crf 16 -g 30 -pix_fmt yuv420p "$out" &
pid=$!
sleep 1.5
echo "recording to $out (pid $pid); touch $stop to stop"
while kill -0 $pid 2>/dev/null; do
  if [ -f "$stop" ]; then kill -INT $pid; break; fi
  sleep 0.5
done
wait $pid 2>/dev/null || true
echo "$out $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")s"
