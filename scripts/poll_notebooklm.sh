#!/usr/bin/env bash
# Poll the active NotebookLM tab until the Audio Overview finishes generating.
# Run via the background runner; you'll be notified on completion. Do NOT
# busy-wait or shorten the interval — generation can take 15+ minutes.
#
# Prints one status line per poll. Exits when "Generating Audio Overview" is no
# longer on the page, or after the cap (~20 min).

MAX_ITERS="${PTTS_POLL_ITERS:-42}"   # 42 * 30s ≈ 21 min
SLEEP_SECS="${PTTS_POLL_SLEEP:-30}"

for i in $(seq 1 "$MAX_ITERS"); do
  status=$(browser-harness <<'PY'
try:
    txt = js("(() => document.body.innerText)()") or ""
    if "Generating Audio Overview" in txt:
        print("GENERATING")
    elif __import__("re").search(r"\b\d{1,2}:\d{2}\b", txt):
        print("LIKELY_READY")
    else:
        print("CHANGED")
except Exception as e:
    print("POLL_ERR:" + str(e)[:80])
PY
)
  echo "poll $i/$MAX_ITERS: $status"
  case "$status" in
    GENERATING) ;;                       # keep waiting
    POLL_ERR:*) ;;                       # transient; keep waiting
    *) echo "STOP: $status"; exit 0 ;;   # generation finished or page changed
  esac
  sleep "$SLEEP_SECS"
done

echo "STOP: TIMEOUT after $MAX_ITERS polls"
exit 0
