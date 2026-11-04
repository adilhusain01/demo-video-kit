#!/usr/bin/env python3
"""One ElevenLabs voice file per narration line, so each line can start on its own cue.

Usage: python3 -I kit/tts.py <project-dir> [line-id ...] [--env-file PATH]
  line ids look like "buy-2" (scene id, then the line's index). With none, every line is (re)made.

The key comes from ELEVENLABS_API_KEY, else --env-file, else the macOS Keychain item "elevenlabs-api-key".
It is read at run time and never printed or written. Store it once, in your own terminal (it prompts):
  security add-generic-password -s elevenlabs-api-key -a "$USER" -w

Voice and model come from project.json ("voice": {"id", "model"}). The default is Sarah, a premade voice:
the free plan refuses library voices over the API.
"""
import json, os, pathlib, subprocess, sys, urllib.error, urllib.request

args = sys.argv[1:]
if not args:
    sys.exit(__doc__)
root = pathlib.Path(args.pop(0)).expanduser().resolve()
env_file = None
if "--env-file" in args:
    i = args.index("--env-file")
    env_file = args[i + 1]
    del args[i : i + 2]

key = os.environ.get("ELEVENLABS_API_KEY")
if not key and env_file:
    for line in pathlib.Path(env_file).expanduser().read_text().splitlines():
        if line.strip().startswith("ELEVENLABS_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
if not key:
    found = subprocess.run(["security", "find-generic-password", "-s", "elevenlabs-api-key", "-w"], capture_output=True, text=True)
    key = found.stdout.strip() or None
if not key:
    sys.exit("No ElevenLabs key. Store it with: security add-generic-password -s elevenlabs-api-key -a \"$USER\" -w")
if not key.startswith("sk_"):
    # ElevenLabs shows two values per key. The 64-character one is the key's ID and is refused with
    # "api_key_id_used_as_api_key". The secret starts with sk_, is about 51 characters, and is shown once.
    sys.exit(f"The stored ElevenLabs value is not a secret key (it does not start with sk_, length {len(key)}). Create a new key and store the sk_ value.")

project = json.loads((root / "project.json").read_text())
voice = project.get("voice", {})
voice_id = os.environ.get("VOICE", voice.get("id", "EXAVITQu4vr4xnSDxMaL"))
model = voice.get("model", "eleven_multilingual_v2")
settings = voice.get("settings", {"stability": 0.55, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True})

scenes = json.loads((root / "scenes.json").read_text())["scenes"]
lines = [(f"{s['id']}-{k}", line["text"]) for s in scenes for k, line in enumerate(s.get("lines", []))]
wanted = set(args) or {lid for lid, _ in lines}
unknown = wanted - {lid for lid, _ in lines}
if unknown:
    sys.exit(f"No such lines: {', '.join(sorted(unknown))}")
out = root / "assets/vo"
out.mkdir(parents=True, exist_ok=True)

for i, (lid, text) in enumerate(lines):
    if lid not in wanted:
        continue
    body = {"text": text, "model_id": model, "voice_settings": settings}
    # The lines around it, so the delivery flows across separate files.
    if i > 0:
        body["previous_text"] = lines[i - 1][1]
    if i < len(lines) - 1:
        body["next_text"] = lines[i + 1][1]
    request = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        data=json.dumps(body).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    try:
        audio = urllib.request.urlopen(request, timeout=120).read()
    except urllib.error.HTTPError as error:
        sys.exit(f"{lid} failed: {error.code} {error.read().decode()[:300]}")
    (out / f"{lid}.mp3").write_bytes(audio)
    print(lid, "ok", len(text.split()), "words")
