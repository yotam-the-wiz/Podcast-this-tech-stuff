---
name: podcast-this-tech-stuff
description: Turns any technical document (PDF, slide/diagram PNGs, plain text, or a Google Doc) into a concise 10–20 minute two-host audio podcast a non-technical listener can follow on the go — calibrated to their background through a few quick questions, with key terms briefly defined and a fast pace. Use when the user wants to understand or listen to a technical doc on the go, says "podcast this", asks to turn a spec / PRD / design doc / paper / diagram into audio, or wants tech material made digestible for a non-technical audience.
---

# podcast-this-tech-stuff

Source doc(s) → calibration questions → tailored brief → high-quality two-host
podcast. Primary engine is **NotebookLM** driven in the user's Chrome (best free
voice quality). Offline fallback is a local `say`-based pipeline.

## Default style (do not skip)

Concise and fast. Explain the main ideas clearly, **briefly define each key term
the first time it appears, then move on**. Assume the listener picks up new
concepts quickly — do not over-explain or belabor points. The goal is "I now get
what's going on" in 10–20 min, not a lecture. The calibration answers only
*adjust* this default; they don't replace it.

## Step 1 — Collect the source(s)

Accept any of: a local PDF, PNG/diagram, `.txt`/`.md`, a Google Doc URL, or pasted
text. Ask the user to upload / paste / give the path or link if not already given.
Note the file type(s) — it changes how NotebookLM ingests them (Step 4).

## Step 2 — Calibrate the listener (ask, then proceed)

Use **one** `AskUserQuestion` call with these questions (defaults are first +
"(Recommended)"). Keep it fast — this is the whole point of the skill.

1. **Listener** — "Who's listening, and how technical are they?"
   - `Non-technical (Recommended)` — smart generalist, not in this domain. Brief term definitions, fast pace. *(the default style above)*
   - `Semi-technical` — knows software broadly, new to this area. Lighter definitions.
   - `Technical, new topic` — minimal definitions; focus on the specific ideas/decisions/tradeoffs.
   - `Complete beginner` — more analogies, define more terms, gentler pace.
2. **Length** — "How long?"
   - `~12 min (Recommended)` · `~8 min tight` · `~18–20 min thorough`
3. **Sources** — "Anything else this episode should pull from? More sources
   usually make a richer episode."
   - `Add more files/links (Recommended)` · `Just this one`

Prefer aggregation: a multi-source episode is more robust, so actively invite
related docs/diagrams/links before generating. If they add more, loop Step 1
until they say they're done. The user may also use "Other" to give a **focus
angle** (what they care about most) — capture it.

## Step 3 — Build the brief

Fill this template from the answers — it drives both engines:

```
AUDIENCE: <listener answer, in plain words>
GOAL: Explain the main ideas so this listener understands what's going on while
commuting. Define each key technical term briefly the first time it appears,
then move on. Assume the listener picks up new concepts fast.
STYLE: Concise, fast-paced, two hosts (a curious host + an expert). No filler,
no recap loops. Conversational, not read-aloud.
LENGTH: ~<N> minutes.
FOCUS: <focus angle, or "the document's core ideas and why they matter">
COVERAGE: Cover every source provided; weave them into one narrative.
```

## Step 4 — Primary engine: NotebookLM (best quality)

Drive NotebookLM in the user's Chrome via `browser-harness`
(https://github.com/browser-use/browser-harness). If it is not installed, use
whatever browser-control tool the agent has, or go straight to Step 5. Full click-by-click
playbook, selectors, and gotchas are in **[REFERENCE.md](REFERENCE.md)** — read it
before driving. High level:

1. `new_tab("https://notebooklm.google.com/")` → confirm the user is logged in
   to their Google account. If bounced to a login wall, **stop and ask** the
   user to sign in; never type credentials.
2. Use a **fresh notebook per episode** ("Create notebook"; don't reuse a stale
   one). Add **all** gathered sources into this one notebook — Drive picker for
   Google Docs, Upload files for local PDF/PNG/text, Copied text for pasted
   text. NotebookLM weaves every source into a single conversation, so loading
   them together is what makes the episode robust.
3. Studio panel → **Customize Audio Overview** → paste the Step 3 brief into the
   instructions box → pick the closest length option → **Generate**.
4. Wait: run `scripts/poll_notebooklm.sh` in the background (generation takes
   ~5–20 min). You'll be notified when it finishes — do not busy-wait.
5. Download via the audio card's **More → Download**, then move the file:
   `~/Downloads/<name>.m4a` → `~/doc2podcast/episodes/<slug>.m4a`.
6. `open -R` the file in Finder and report duration (`afinfo`).

## Step 5 — Fallback: local `say` pipeline (offline / NotebookLM blocked)

Use only if there's no internet, NotebookLM errors out, or the user asks for
offline. You (Claude) read the source directly — the Read tool handles PDF, PNG,
and text — and **write the two-host script yourself**, obeying the Step 3 brief
(speaker lines prefixed `A:` / `B:`). Then:

```
python3 <this skill's directory>/scripts/local_fallback.py \
  <script.txt> "<episode-slug>"
```

It voices A/B with distinct macOS voices, stitches, and writes
`~/doc2podcast/episodes/<slug>.m4a`. Tell the user this is the lower-quality
fallback and offer to re-run via NotebookLM when back online.

## Output conventions

- All episodes land in `~/doc2podcast/episodes/`.
- Name files from the source title, slugified (e.g. `auth-rewrite-rfc.m4a`).
- Always end by revealing the file in Finder and stating its length.
