# REFERENCE — Driving NotebookLM with browser-harness

Field-tested playbook. NotebookLM's own UI (top bar, Sources panel, Studio
panel, Customize dialog) is **app DOM** — query it with `js(...)` and click by
the returned coordinates. The Google **Drive picker** is a **cross-origin
iframe** — DOM queries return nothing there, so use `capture_screenshot()` +
`click_at_xy()` (clicks pass through iframes at the compositor level).

Always: act → `capture_screenshot()` → verify → next. Re-screenshot after every
meaningful click before assuming it worked.

## 0. Conventions

- Every `browser-harness` call uses the heredoc form (`browser-harness <<'PY' … PY`).
- First navigation is `new_tab(url)` — never `goto_url` (it clobbers the user's tab).
- `click_at_xy` takes **page CSS coordinates** (what `getBoundingClientRect`
  returns), not screenshot-image pixels. Get coords from a DOM query, then click
  them directly. For the Drive picker (no DOM), read the pixel off the screenshot.

## 1. Open + auth check

```
browser-harness <<'PY'
new_tab("https://notebooklm.google.com/")
wait_for_load()
import time; time.sleep(3)
print(page_info()); capture_screenshot("/tmp/ptts_1.png")
PY
```

A fresh visit usually auto-creates an empty notebook and shows the
"Create Audio and Video Overviews" add-source dialog. If you see a Google login
page instead, **stop and ask the user to log in** — never type credentials.

## 2. Add the source(s)

The add-source dialog has a row: **Upload files | Websites | Drive | Copied text**.
Find exact coords (these are app DOM):

```
browser-harness <<'PY'
print(js(r"""(() => {
  const out=[];
  for (const e of document.querySelectorAll('button,[role=button],span,div')) {
    const t=(e.innerText||'').trim();
    if(['Drive','Upload files','Copied text','Add sources'].includes(t)){
      const r=e.getBoundingClientRect();
      if(r.width>0&&r.height>0) out.push({t,x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});
    }
  }
  return JSON.stringify(out);
})()"""))
PY
```

Then by source type:

- **Google Doc** → click `Drive`. A Drive picker iframe opens (give it ~6 s).
  From here use **screenshots only**. Either click the doc's tile in "Recent",
  or click the search box and type the doc title to filter. Select the tile
  (bottom bar shows "N selected"), then click the blue **Insert** button at the
  picker's bottom-right. The notebook auto-titles itself once ingested.
- **Local PDF / PNG / txt / md** → click `Upload files`. A native file chooser
  opens; use the `file_upload` helper or set the `<input type=file>` value (see
  browser-harness `interaction-skills/uploads.md`). Multiple files: repeat
  **Add sources → Upload files**.
- **Pasted text** → click `Copied text`, paste into the textarea, confirm.

Verify each source appears (checked) in the left **Sources** panel before moving on.

## 3. Customize + generate the Audio Overview

The Studio panel (right side) is app DOM. Find the customize control:

```
browser-harness <<'PY'
print(js(r"""(() => {
  const out=[];
  for (const e of document.querySelectorAll('[aria-label],button,[role=button]')) {
    const l=(e.getAttribute('aria-label')||'').trim();
    if(/Audio Overview/i.test(l)){
      const r=e.getBoundingClientRect();
      if(r.width>0&&r.height>0) out.push({l,x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});
    }
  }
  return JSON.stringify(out);
})()"""))
PY
```

Click the one labelled **"Customize Audio Overview"** (a chevron next to the
"Audio Overview" tile). A dialog opens with an instructions textarea and usually
a length selector (Shorter / Default / Longer).

1. Type the **Step 3 brief** into the textarea. Find it via DOM:
   `document.querySelector('textarea')` → focus it, then use the harness key/typing
   input (or set `.value` and dispatch an `input` event) to enter the brief.
2. Pick the length option closest to the requested minutes (Longer for
   ~18–20 min, Default for ~12, Shorter for ~8).
3. Click **Generate** / **Create**.

If there is no Customize control (older UI), click the **Audio Overview** tile
directly — it generates with defaults. The brief still helps if you can paste it
into the notebook chat as a steering note before generating, but prefer the
Customize dialog.

Confirm generation started: page text contains
`Generating Audio Overview... Come back in a few minutes`.

## 4. Wait for generation

Generation took ~15 min in testing; allow up to ~20. Run the poller in the
**background** and let the completion notification wake you — do not sleep-loop
or proactively re-check:

```
~/.claude/skills/podcast-this-tech-stuff/scripts/poll_notebooklm.sh
```

(run it with the background runner). It exits when the "Generating Audio
Overview" text disappears or after the cap.

## 5. Download + file the episode

When done, the audio card appears low in the Studio panel with **Play**,
**Interactive mode**, and **More (more_vert)** buttons. Find + open the More menu:

```
browser-harness <<'PY'
print(js(r"""(() => {
  const out=[];
  for (const e of document.querySelectorAll('button,[role=button],[aria-label]')) {
    const l=(e.getAttribute('aria-label')||'').trim();
    const r=e.getBoundingClientRect();
    if(r.width>0&&r.height>0 && r.x>950 && /^(Play|More|Interactive mode)$/.test(l))
      out.push({l,x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});
  }
  return JSON.stringify(out);
})()"""))
PY
```

Click **More**, wait ~2 s, then query menu items and click the one whose text
matches `Download` (the menu typically lists Rename / Download / Share / Delete):

```
browser-harness <<'PY'
print(js(r"""(() => {
  const out=[];
  for (const e of document.querySelectorAll('[role=menuitem],button,li,[role=button]')) {
    const t=(e.innerText||'').trim();
    const r=e.getBoundingClientRect();
    if(r.width>0&&r.height>0 && /download|rename|delete|share/i.test(t))
      out.push({t:t.replace(/\n/g,'|').slice(0,30),x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});
  }
  return JSON.stringify(out);
})()"""))
PY
```

The browser saves to `~/Downloads/` (a long auto-generated `.m4a` name, ~40 MB,
stereo 256 kbps). Find the freshest and file it:

```
f=$(ls -t ~/Downloads/*.m4a | head -1)
mkdir -p ~/doc2podcast/episodes
mv "$f" ~/doc2podcast/episodes/<slug>.m4a
afinfo ~/doc2podcast/episodes/<slug>.m4a | grep -Ei 'estimated duration'
open -R ~/doc2podcast/episodes/<slug>.m4a
```

Report the path and duration to the user.

## Gotchas

- The add-source dialog's heading text animates ("…your documents" →
  "…YouTube videos"). That's cosmetic; ignore it. A click that "did nothing"
  usually means wrong coords, not a failed click — re-query the DOM.
- Drive picker = cross-origin iframe → DOM queries return `[]`. Switch to
  screenshots + coordinate clicks the moment you click "Drive".
- `click_at_xy` wants page CSS coords; screenshots may be rendered at a
  different scale. Prefer DOM-derived coords for app UI; only eyeball pixels for
  the Drive picker.
- Generation can take 15+ min for a dense doc. The poller's "DONE" can briefly
  read `UNKNOWN` before the player renders — re-screenshot to confirm the audio
  card with Play/More is present before downloading.
- Don't reuse a stale notebook across runs unless the user wants a series in one
  notebook — default to a fresh notebook per source set ("Create notebook").
