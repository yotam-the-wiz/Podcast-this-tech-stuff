# podcast-this-tech-stuff

Turn any technical document into a concise **10–20 minute, two-host audio
podcast** a non-technical listener can follow on the go.

Feed it a PDF, slide/diagram PNGs, plain text, or a Google Doc. It asks a few
quick questions to calibrate to *your* background, then produces a fast-paced
two-host episode that explains the main ideas, briefly defines each key term the
first time it comes up, and gets you to "I get what's going on" — without the
lecture.

This is a [Claude Code](https://claude.com/claude-code) **agent skill**.

## What it does

1. **Collects your source(s)** — PDF, PNG/diagram, `.txt`/`.md`, a Google Doc
   URL, or pasted text. Multiple sources get woven into one narrative.
2. **Calibrates the listener** — a single set of quick questions: how technical
   is the audience, how long should it run, any other sources or focus angle.
3. **Builds a brief** from your answers that drives the generation.
4. **Generates the episode** with Google **NotebookLM** (best free voice
   quality), driven automatically in your own Chrome.
5. **Files the result** — a `.m4a` lands in `~/doc2podcast/episodes/`, revealed
   in Finder with its duration.

If NotebookLM is unreachable (offline, blocked), it falls back to a local
macOS `say`-based pipeline — lower quality, but works without internet.

## Requirements

- **Claude Code** (the CLI/agent that runs skills).
- **macOS** — the offline fallback uses the built-in `say` voices and `afinfo`.
- **Google Chrome**, logged in to a Google account with **NotebookLM** access
  (for the primary, high-quality path).
- **[browser-harness](https://github.com/browser-use/browser-use)** — the
  CDP-based browser-control helper the skill uses to drive NotebookLM in your
  Chrome. Must be installed and on `$PATH`.
- **Python 3** — for the local fallback pipeline.

The high-quality path needs a working NotebookLM login in your Chrome. If the
skill hits a Google login wall it will stop and ask you rather than enter
credentials.

## Install

Drop this directory into your Claude Code skills folder so it's discoverable:

```bash
git clone <this-repo-url> ~/.claude/skills/podcast-this-tech-stuff
```

(Or copy the folder there manually.) Claude Code picks up the skill from its
`SKILL.md` automatically — no extra registration step.

## Usage

In Claude Code, just ask in natural language. Triggers include:

- "podcast this" (with a doc attached or path/link given)
- "turn this spec/PRD/design doc/paper into audio"
- "I want to listen to this on my commute"
- "make this technical doc digestible for a non-technical person"

The skill will ask you a few calibration questions, then generate. NotebookLM
generation takes roughly 5–20 minutes; the skill polls in the background and
notifies you when the episode is ready — you don't have to wait around.

### Output

- All episodes land in `~/doc2podcast/episodes/`.
- Files are named from the source title, slugified
  (e.g. `auth-rewrite-rfc.m4a`).
- The skill ends by revealing the file in Finder and stating its length.

## Project layout

| File | Purpose |
|---|---|
| `SKILL.md` | The skill definition Claude Code loads — workflow, calibration questions, style defaults. |
| `REFERENCE.md` | Field-tested playbook for driving NotebookLM via browser-harness (selectors, gotchas). |
| `scripts/poll_notebooklm.sh` | Background poller that waits for NotebookLM generation to finish. |
| `scripts/local_fallback.py` | Offline two-host `say` pipeline (voices A/B, stitches, writes the `.m4a`). |

## License

MIT — see `LICENSE`.
