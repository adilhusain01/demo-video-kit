#!/usr/bin/env python3
"""Contact sheets of a take, for finding the exact second each event appears (the cues in scenes.json).

Usage:
  python3 -I kit/sheet.py <take.mp4> <out.png> --every 3 [--from 0 --to 60] [--crop w:h:x:y] [--cols 3] [--width 900]
  python3 -I kit/sheet.py <take.mp4> <out.png> --at 24.5,25,25.5,26 [--crop ...]

Read the sheet as an image. Narrow down: every 3 s to find the window, then every 0.5 s inside it.
Do not try to detect events from pixel counts: a blinking cursor flips the numbers every half second.
"""
import pathlib, subprocess, sys, tempfile


def option(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def probe(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    take, out = sys.argv[1], sys.argv[2]
    crop, cols, width = option("--crop"), max(2, int(option("--cols", 3))), int(option("--width", 900))
    if option("--at"):
        times = [float(x) for x in option("--at").split(",")]
    else:
        step, start, end = float(option("--every", 3)), float(option("--from", 0)), float(option("--to", probe(take)))
        times, t = [], start
        while t <= end:
            times.append(round(t, 2))
            t += step
    with tempfile.TemporaryDirectory() as tmp:
        frames = []
        for t in times:
            f = f"{tmp}/{t:09.2f}.png"
            vf = (f"crop={crop}," if crop else "") + f"scale={width}:-2"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t), "-i", take, "-frames:v", "1", "-vf", vf, f], check=True)
            frames.append(f)
        while len(frames) % cols:
            frames.append(frames[-1])
        rows = len(frames) // cols
        args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        for f in frames:
            args += ["-i", f]
        graph = "".join(f"{''.join(f'[{r * cols + c}]' for c in range(cols))}hstack={cols}[r{r}];" for r in range(rows))
        graph += "".join(f"[r{r}]" for r in range(rows)) + (f"vstack={rows}" if rows > 1 else "null")
        subprocess.run(args + ["-filter_complex", graph, out], check=True)
    print(out, "times:", ", ".join(f"{t:g}" for t in times), f"({cols} per row, left to right)")


if __name__ == "__main__":
    main()
