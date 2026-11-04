#!/usr/bin/env python3
"""Cut a demo video from raw takes, cards, captions and per-line voice files.

Usage: python3 -I kit/build.py <project-dir> [--stills]
  --stills   (re)render the title and end cards, the caption bands and the speed labels first.

A project folder holds project.json (theme, default crop, card text), scenes.json (the cut), raw/ (the takes)
and assets/vo/ (voice files from tts.py). See docs/WORKFLOW.md for the format.

Rules the cut follows, learned the hard way:
- Each voice line starts at its cue ("at", seconds into its clip), when the event it describes is on screen.
  A line that would overlap the one before waits for it. The voice never runs ahead of the footage.
- A scene lasts as long as its footage, or longer when its last line needs it; then the last frame is held,
  so nothing is cut off mid-event.
- Without voice files, line lengths are estimated at 2.6 words a second, so the edit can be checked first.
"""
import json, pathlib, re, subprocess, sys, urllib.parse

KIT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1920, 1080
TAIL = 0.7          # silence after a scene's last line
GAP = 0.15          # silence between lines that queue up
FPS = 30


def run(args):
    subprocess.run(args, check=True)


def probe(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout)


def piecewise(keys, index):
    """An ffmpeg expression of t (seconds) that moves linearly between keyframes [(t, v...)] on value `index`."""
    t = f"(on/{FPS})"
    expr = str(keys[-1][index])
    for (t0, *a), (t1, *b) in reversed(list(zip(keys, keys[1:]))):
        v0, v1 = a[index - 1], b[index - 1]
        span = max(t1 - t0, 1e-3)
        expr = f"if(lt({t},{t1}),{v0}+({v1}-{v0})*({t}-{t0})/{span},{expr})"
    return f"if(lt({t},{keys[0][0]}),{keys[0][index]},{expr})"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root = pathlib.Path(sys.argv[1]).expanduser().resolve()
    project = json.loads((root / "project.json").read_text())
    scenes = json.loads((root / "scenes.json").read_text())["scenes"]
    theme = json.loads((KIT / "kit/themes" / f"{project.get('theme', 'stockroom')}.json").read_text())
    band = int(project.get("band", 120))
    default_crop = project.get("crop")
    vo_dir, caps, out_dir = root / "assets/vo", root / "assets/caps", root / "build"
    for d in (vo_dir, caps, out_dir):
        d.mkdir(parents=True, exist_ok=True)

    def line_length(scene, k, text):
        mp3 = vo_dir / f"{scene['id']}-{k}.mp3"
        return probe(mp3) if mp3.exists() else len(text.split()) / 2.6

    plan = []
    for s in scenes:
        timed, free = [], 0.0
        for k, line in enumerate(s.get("lines", [])):
            a = max(line["at"], free)
            b = a + line_length(s, k, line["text"])
            timed.append((line["text"], a, b))
            free = b + GAP
        spoken_end = timed[-1][2] + TAIL if timed else 0.0
        footage = s["seconds"] if "card" in s else (s["out"] - s["in"]) / s.get("speed", 1)
        plan.append({**s, "dur": round(max(footage, spoken_end) + s.get("hold", 0), 3), "timed": timed})

    if "--stills" in sys.argv:
        render_stills(root, project, theme, band, plan, caps)

    clips = []
    for p in plan:
        clip = out_dir / f"{p['id']}.mp4"
        if "card" in p:
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-t", str(p["dur"]), "-i", str(caps / f"card-{p['card']}.png"),
                 "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS), str(clip)])
        else:
            crop = p.get("crop")
            crop = default_crop if crop is True else crop
            src_w, src_h = (int(v) for v in (crop.split(":")[:2] if crop else probe_size(root / p["src"])))
            area_h = H - band - 20
            fit_h = area_h - area_h % 2
            fit_w = int(src_w * fit_h / src_h) // 2 * 2
            if fit_w > W:
                fit_w = W
                fit_h = int(src_h * W / src_w) // 2 * 2
            speed = p.get("speed", 1)
            footage = (p["out"] - p["in"]) / speed
            hold = max(0.0, p["dur"] - footage)
            chain = [f"crop={crop}"] if crop else []
            chain += [f"setpts=PTS/{speed}", f"fps={FPS}"]
            if p.get("zoom"):
                # Keyframes [t, scale, focus x, focus y], focus as a fraction of the frame. zoompan reads the
                # full-resolution take, so zoomed text stays sharp.
                keys = p["zoom"]
                z, fx, fy = piecewise(keys, 1), piecewise(keys, 2), piecewise(keys, 3)
                chain.append(f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,({fx})*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,({fy})*ih-ih/zoom/2))':d=1:s={fit_w}x{fit_h}:fps={FPS}")
            else:
                chain.append(f"scale={fit_w}:{fit_h}:flags=lanczos")
            chain += [f"pad={W}:{H}:(ow-iw)/2:{(H - band - fit_h) // 2}:color={theme['frame_bg']}", f"tpad=stop_mode=clone:stop_duration={hold:.3f}", "format=yuv420p"]
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(p["in"]), "-to", str(p["out"]), "-i", str(root / p["src"]),
                 "-vf", ",".join(chain), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS), "-t", str(p["dur"]), str(clip)])
        # Captions and the speed label, each shown while its line is spoken.
        overlays = [(caps / f"{p['id']}-{k}.png", a, b + 0.25) for k, (_, a, b) in enumerate(p["timed"])]
        inputs, graph, last = ["-i", str(clip)], "", "0:v"
        for k, (png, a, b) in enumerate(overlays):
            inputs += ["-i", str(png)]
            graph += f"[{last}][{k + 1}:v]overlay=0:{H - band}:enable='between(t,{a:.2f},{b:.2f})'[v{k}];"
            last = f"v{k}"
        if p.get("label"):
            inputs += ["-i", str(caps / f"{p['id']}-label.png")]
            graph += f"[{last}][{len(overlays) + 1}:v]overlay=W-w-60:40[vl];"
            last = "vl"
        if graph:
            captioned = out_dir / f"{p['id']}.cap.mp4"
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex", graph.rstrip(";"), "-map", f"[{last}]",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS), str(captioned)])
            clip = captioned
        clips.append((clip, p))

    (out_dir / "list.txt").write_text("".join(f"file '{c}'\n" for c, _ in clips))
    silent = out_dir / "silent.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(out_dir / "list.txt"), "-c", "copy", str(silent)])
    starts, t = {}, 0.0
    for _, p in clips:
        starts[p["id"]] = t
        t += p["dur"]
    name = project.get("name", root.name)
    voiced = [(p, a, vo_dir / f"{p['id']}-{k}.mp3") for _, p in clips for k, (_, a, _) in enumerate(p["timed"]) if (vo_dir / f"{p['id']}-{k}.mp3").exists()]
    if voiced:
        inputs, mix = ["-i", str(silent)], ""
        for n, (p, a, mp3) in enumerate(voiced):
            inputs += ["-i", str(mp3)]
            ms = int((starts[p["id"]] + a) * 1000)
            mix += f"[{n + 1}:a]adelay={ms}|{ms}[a{n}];"
        mix += "".join(f"[a{n}]" for n in range(len(voiced))) + f"amix=inputs={len(voiced)}:normalize=0,apad[aout]"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex", mix, "-map", "0:v", "-map", "[aout]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(root / f"{name}.mp4")])
    else:
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(silent), "-c", "copy", str(root / f"{name}-silent.mp4")])

    # Captions as a file, for YouTube, and the narration as plain text.
    def stamp(x):
        return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}".replace(".", ",")
    srt, n = [], 1
    for _, p in clips:
        for text, a, b in p["timed"]:
            srt.append(f"{n}\n{stamp(starts[p['id']] + a)} --> {stamp(starts[p['id']] + b + 0.25)}\n{text}\n")
            n += 1
    (root / f"{name}.srt").write_text("\n".join(srt))
    (root / "narration.txt").write_text("\n".join(line["text"] for _, p in clips for line in p.get("lines", [])))
    (root / "build/timeline.json").write_text(json.dumps({p["id"]: {"start": round(starts[p["id"]], 2), "dur": p["dur"], "lines": [[round(starts[p["id"]] + a, 2), text] for text, a, _ in p["timed"]]} for _, p in clips}, indent=1))
    print(f"total {t:.1f}s, {len(voiced)} voice files")
    for _, p in clips:
        print(f"  {p['id']:10} {starts[p['id']]:6.1f}s  {p['dur']:5.1f}s  lines end {p['timed'][-1][2] if p['timed'] else 0:5.1f}s")


def probe_size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    return out.strip().split(",")


def render_stills(root, project, theme, band, plan, caps):
    """Cards, caption bands and labels as PNGs, through a headless browser so the theme's fonts are used."""
    fonts = KIT / "node_modules"
    cards = project.get("cards", {})
    title, end = cards.get("title", {}), cards.get("end", {})
    mark = (f'<svg class="mark" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="{theme["mark_fill"]}"/>'
            f'<circle cx="10" cy="11" r="3.2" fill="{theme["mark_accent"]}"/><circle cx="22" cy="11" r="3.2" fill="{theme["mark_accent"]}"/>'
            f'<circle cx="16" cy="22" r="3.2" fill="none" stroke="{theme["mark_line"]}" stroke-width="1.6" stroke-dasharray="2 2"/>'
            f'<path d="M13 11h6M11.6 13.8 14.2 19M20.4 13.8 17.8 19" stroke="{theme["mark_line"]}" stroke-width="1.6" stroke-linecap="round"/></svg>') if project.get("mark", True) else ""
    values = {
        **{k: str(v) for k, v in theme.items() if not k.startswith("_")},
        "font_display": "file://" + str(fonts / theme["font_display"]),
        "font_body": "file://" + str(fonts / theme["font_body"]),
        "font_mono": "file://" + str(fonts / theme["font_mono"]),
        "band_height": str(band),
        "mark": mark,
        "title_headline": title.get("headline", ""),
        "title_sub": title.get("sub", ""),
        "end_headline": end.get("headline", ""),
        "end_lines": "<br>".join(end.get("lines", [])),
        "end_sub": end.get("sub", ""),
    }
    html = (KIT / "kit/frame.html").read_text()
    for key, value in values.items():
        html = html.replace("{{" + key + "}}", value)
    page = root / "build/frame.html"
    page.write_text(html)
    env = {"AGENT_BROWSER_SESSION": "demo-video-kit-stills", "PATH": subprocess.run(["bash", "-lc", "echo $PATH"], capture_output=True, text=True).stdout.strip()}

    def shoot(query, path, selector=None, size=(W, H)):
        url = "file://" + str(page) + "?" + urllib.parse.urlencode(query)
        for args in (["set", "viewport", str(size[0]), str(size[1])], ["open", url], ["wait", "300"]):
            subprocess.run(["agent-browser", *args], env=env, check=True, capture_output=True)
        subprocess.run(["agent-browser", "screenshot", *([selector] if selector else []), str(path)], env=env, check=True, capture_output=True)

    for card in ("title", "end"):
        if any(p.get("card") == card for p in plan):
            shoot({"mode": card}, caps / f"card-{card}.png")
    for p in plan:
        for k, (text, _, _) in enumerate(p["timed"]):
            shoot({"mode": "cap", "text": text}, caps / f"{p['id']}-{k}.png", "#band", (W, band))
        if p.get("label"):
            shoot({"mode": "label", "text": p["label"]}, caps / f"{p['id']}-label.png", "#label", (900, 120))
    subprocess.run(["agent-browser", "close"], env=env, capture_output=True)


if __name__ == "__main__":
    main()
