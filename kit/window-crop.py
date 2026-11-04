#!/usr/bin/env python3
"""Find a window's crop in the screen capture by its background colour (a terminal, a dark card).

Usage: python3 -I kit/window-crop.py --color 161b1e [--take raw/take.mp4 --at 5] [--tolerance 10]
With no --take it grabs one frame of the live screen. Prints w:h:x:y (even numbers) for scenes.json or
project.json "crop". The capture is in the screen's backing pixels (3600x2338 on a 14-inch MacBook Pro at
"More Space"), not points, so never guess a crop from window coordinates.
"""
import subprocess, sys


def option(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def frame(take, at):
    if take:
        src = ["-ss", str(at), "-i", take]
    else:
        dev = subprocess.run("ffmpeg -hide_banner -f avfoundation -list_devices true -i '' 2>&1 | sed -n 's/.*\\[\\([0-9]*\\)\\] Capture screen 0.*/\\1/p' | head -1", shell=True, capture_output=True, text=True).stdout.strip()
        src = ["-f", "avfoundation", "-framerate", "30", "-capture_cursor", "0", "-pixel_format", "uyvy422", "-i", f"{dev}:none"]
    size = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", *src, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", "-"], input=size, capture_output=True, check=True).stdout.decode().strip().split(",")
    w, h = int(probe[0]), int(probe[1])
    step = 4  # detect on a quarter-size frame, then scale back up
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "-", "-vf", f"scale={w // step}:{h // step}:flags=neighbor", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], input=size, capture_output=True, check=True).stdout
    return raw, w // step, h // step, step


def main():
    color = option("--color")
    if not color:
        sys.exit(__doc__)
    target = tuple(int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    tol = int(option("--tolerance", 10))
    raw, w, h, step = frame(option("--take"), option("--at", 1))

    def near(i):
        return all(abs(raw[i + c] - target[c]) <= tol for c in range(3))

    rows = [sum(1 for x in range(w) if near((y * w + x) * 3)) for y in range(h)]
    cols = [sum(1 for y in range(h) if near((y * w + x) * 3)) for x in range(w)]
    if max(rows) == 0:
        sys.exit(f"no pixels near #{color.lstrip('#')} in the frame; is the window in front?")
    ys = [y for y, n in enumerate(rows) if n > max(rows) * 0.5]
    xs = [x for x, n in enumerate(cols) if n > max(cols) * 0.5]
    x0, x1, y0, y1 = xs[0] * step, (xs[-1] + 1) * step, ys[0] * step, (ys[-1] + 1) * step
    # Trim the rounded corners and a few pixels of edge.
    x0, y0, x1, y1 = x0 + 8, y0 + 8, x1 - 8, y1 - 8
    cw, ch = (x1 - x0) // 2 * 2, (y1 - y0) // 2 * 2
    print(f"{cw}:{ch}:{x0}:{y0}")


if __name__ == "__main__":
    main()
