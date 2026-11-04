# Prompts and writing rules

## Starting a video with Claude Code

Paste this, filled in, into a Claude Code session on the Mac that will record:

```
Make a demo video for <product> with the demo-video skill (kit at ~/Documents/Projects/mine/demo-video-kit).
What it must prove, one claim per line:
- <claim 1, e.g. the agent's purchase is co-signed and delivered>
- <claim 2, e.g. a payment over the cap is refused at the key>
Where it runs: <host and repo path, the public URL>.
Limits: <length, e.g. under 3 minutes>; <capped or costly actions to do only once>.
Theme: <stockroom | gruvbox | a new one from the product's tokens>.
Voice: ElevenLabs, key in the Keychain as elevenlabs-api-key.
Record everything for real, measure every cue from the footage, show me the cut before any upload.
```

## Narration rules

- One line per event, spoken when the event is on screen. Two short sentences beat one long one.
- Name things the way the product does on screen ("the co-signer", "the counter"), so the viewer can match words to text.
- Say what the viewer is about to see before a long wait, and what happened once it shows.
- State limits honestly in the voice when they matter ("Bitrefill's test top-up", "8x speed").
- No hype words, no "revolutionary", no "seamless". No em dashes in captions.
- Run every line through the humanizer skill before generating voice: it removes the tells that make narration sound generated.
- Read the script aloud at about 2.6 words a second; that is the pace the estimate in build.py assumes.

## Card text

- Title: what it is in one line, set like the product's own hero. A sub line that says it was recorded live, and when.
- End: the name, where to get it (repo URL), one line of what's next or upstream, where it was built and the licence.

## The cut, as a reviewer

Before calling a cut done, look at `build/cues.png` and ask of every frame: does the screen already show what this line says? Then watch it once at full speed with sound.
