#!/usr/bin/env python3
"""Check a finished cut before anyone watches it.

Usage: python3 -I kit/check.py <project-dir>
Prints length, size, loudness and any overlapping voice lines, and writes build/cues.png: one frame
half a second after each line starts, captioned with the line, so you can see that the screen already shows
what the voice is saying. Read cues.png as an image; fix a wrong cue in scenes.json and rebuild.
"""
import json, pathlib, subprocess, sys, tempfile


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root = pathlib.Path(sys.argv[1]).expanduser().resolve()
    name = json.loads((root / "project.json").read_text()).get("name", root.name)
    video = root / f"{name}.mp4"
    if not video.exists():
        video = root / f"{name}-silent.mp4"
    info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height", "-of", "json", str(video)], capture_output=True, text=True, check=True).stdout
    data = json.loads(info)
    print(video.name, f"{float(data['format']['duration']):.1f}s", [(s.get("codec_name"), s.get("width"), s.get("height")) for s in data["streams"]])
    loud = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summary = [l.strip() for l in loud.splitlines() if l.strip().startswith(("I:", "Peak:", "LRA:"))][-3:]
    print("loudness:", " | ".join(summary) or "no audio", "(aim for about -16 to -14 LUFS, peak below -1 dB)")

    timeline = json.loads((root / "build/timeline.json").read_text())
    lines = sorted((t, text) for scene in timeline.values() for t, text in scene["lines"])
    vo = root / "assets/vo"
    overlaps = 0
    ends = []
    for sid, scene in timeline.items():
        for k, (t, _) in enumerate(scene["lines"]):
            mp3 = vo / f"{sid}-{k}.mp3"
            if mp3.exists():
                d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)], capture_output=True, text=True).stdout)
                ends.append((t, t + d))
    ends.sort()
    for (a0, b0), (a1, _) in zip(ends, ends[1:]):
        if a1 < b0 - 0.01:
            overlaps += 1
    print("overlapping voice lines:", overlaps)

    with tempfile.TemporaryDirectory() as tmp:
        frames = []
        for i, (t, text) in enumerate(lines):
            f = f"{tmp}/{i:03d}.png"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t + 0.5:.2f}", "-i", str(video), "-frames:v", "1", "-vf", "scale=640:-2", f], check=True)
            frames.append(f)
        cols = 4
        while len(frames) % cols:
            frames.append(frames[-1])
        rows = len(frames) // cols
        args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        for f in frames:
            args += ["-i", f]
        graph = "".join(f"{''.join(f'[{r * cols + c}]' for c in range(cols))}hstack={cols}[r{r}];" for r in range(rows)) + "".join(f"[r{r}]" for r in range(rows)) + (f"vstack={rows}" if rows > 1 else "null")
        subprocess.run(args + ["-filter_complex", graph, str(root / "build/cues.png")], check=True)
    print("cue sheet:", root / "build/cues.png", f"({len(lines)} lines, {cols} per row, in order; each frame is 0.5 s after its line starts)")


if __name__ == "__main__":
    main()
