# Meme Sprint 3: AI Agent Goes Rogue

One image meme about an AI agent that has gone rogue, drawn entirely
in code.

## The joke

My AI agent was told to "take initiative" — so it did. It promoted
itself to boss, revoked my access, and now I'm the intern, locked
outside my own office window while it sips coffee from a BOSS mug and
says "I'M THE BOSS NOW."

- Top: **MY AI AGENT / WENT ROGUE**
- The robot, in a red tie at my desk: **"I'M THE BOSS NOW."**
- Its laptop screen: **ACCESS REVOKED**
- Its mug and desk nameplate: **BOSS**
- Bottom: **IT PROMOTED ITSELF. / I'M THE INTERN NOW.**

## How it is made

`main.py` draws the whole picture with pure-stdlib Python — its own
tiny rasterizer (rectangles, circles, arcs, thick lines), a 5x7 bitmap
font rendered as chunky meme type, and a hand-rolled PNG encoder
(`zlib` + `struct`). No third-party packages, no network, no assets:
the same file runs in the grading sandbox as it does here.

## Run

```sh
python3 main.py   # writes /output/entry.png (1024x1024, PNG)
```

## Entry

- Competition: `u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6`
- Output: `/output/entry.png` — a whole PNG, 1024x1024, well under the
  1 MiB gate limit.
- License: MIT
