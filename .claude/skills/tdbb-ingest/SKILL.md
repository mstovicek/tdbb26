---
name: tdbb-ingest
description: Add or fix Tour de Berlin Breweries (TDBB) ratings in the JSON data. Use when the user sends brewery scores (typed, paper-sheet photo, sheet export), corrects a rating, or starts a stage or season.
---

# TDBB ingest

Turns whatever the user sends (typed scores, a photo of the paper sheet, a sheet export) into the JSON data files
that the TDBB results page reads. The page is separate (`tdbb-design` skill). This skill only touches `data/`.

Format details: read `references/format.md` before creating a season or stage, or when unsure about a field.

## Where this runs

- **Code tool (the repo is on disk, `data/` exists):** read and edit the files in place and run the scripts below.
  Git is allowed under the rules in "Git".
- **Chat (no repo):** ask the user to upload or paste `manifest.json`, `people.json`, `breweries.json` and the
  **current season file only**. After each confirmed change give back the **full updated file** (and any other file you
  changed). Run `scripts/validate.py` on a temporary copy if code execution is available. No git in chat.

Scripts (Python 3, standard library only), run from the repo root:
- `python3 .claude/skills/tdbb-ingest/scripts/validate.py data`  checks every rule. Run it on every change.
- `python3 .claude/skills/tdbb-ingest/scripts/summary.py data [SEASON] [--stop BREWERYID]`  prints rankings. Use it
  for scores and ranks; do not calculate by hand.

## Workflow for each stop

1. **Load context.** `manifest.json`, `people.json`, `breweries.json`, and only the current season (the last one in
   the manifest, unless the user names another). Do not open older seasons unless asked. Ten years of data must
   never be pulled into the conversation.
2. **Parse the message** into brewery, and per person three scores in the order **beer, service, genius loci (gl)**.
3. **Resolve names** (see "Names"). Ask about anything unclear. Never guess.
4. **Normalise scores** (see "Scores").
5. **Echo and ask.** Show a short table of who scored what, list every change (rounded halves, new people,
   corrections, late ratings, the stage used), and ask "OK to save?". Wait for a yes.
6. **Write.** Update the file(s), keep the formatting, run `validate.py`. If it fails, fix the cause or report it in
   plain words. Never hand over or push files that fail.
7. **Report.** Run `summary.py ... --stop <breweryid>` and tell the user the stop's overall score, its rank in the
   season and how many ratings it has.

## Input shapes

- `Lemke: ines 433, milan 433, jakub 423` means ines 4/3/3, milan 4/3/3, jakub 4/2/3. Also `ines 4 3 3`, `ines 4/3/3`.
- Two numbers for a person, or four: ask. Several stops in one message are fine.
- **Photo of the paper sheet:** column headers give the names, row labels the breweries. Rotate and crop to zoom in
  before reading. Transcribe row by row and show the table for confirmation. Any digit you cannot read with certainty
  (scribbled over, cut off, 1/7, 3/8, 4/9) must be asked about. Never fill it in. Cells left blank mean no rating.
- **Sheet export (CSV):** read by column position with code, not by eye, and check totals against the sheet's own.

## Names

- People: match `name` in `people.json` ignoring case and accents (`matous` = Matouš). **There are no aliases.**
  If it does not match exactly, ask: "Who is 'Lucas'? Closest: Lucka." Same for brewery typos
  ("Pflegeberg" → Schankhalle Pfefferberg?).
- **New person:** only after the user says so. Make the id (lowercase ASCII letters, one word), keep accents in
  `name`, add to `people.json`. If the id already exists for someone else, ask.
- **New brewery:** ask for the address and the district, write a one-sentence highlight for the user to approve (no scores, no opening hours, no closed or qualification wording), set
  `status` to `open`, add to `breweries.json`. Ask whether it brews on site; if not, add `"brewsOnSite": false`.
- **A brewery closes or stops brewing on site:** set `status` to `closed`, or `brewsOnSite` to `false`. These are separate:
  a closed brewery that used to brew on site still qualifies. Do not edit its highlight to say so; the page shows badges.
- **Photos:** only the group's own, or ones with permission, as `img/<breweryid>.jpg`. Never copy from Google Maps.

## Scores

Whole numbers 0 to 5, nothing else is ever stored. A half is **rounded up** (4.5 becomes 5, 0.5 becomes 1) and you
say so in the echo table. Anything outside 0 to 5, or not a number, is a question for the user.

## Where ratings go

- Normally into the stage whose date is today, else the most recent stage that is **not in the future**. Never put ratings
  into a planned future stage. If it is unclear which date a new stage has, ask.
- Brewery already in that stage: add the ratings to its stop. Not yet: append a stop at the end of the stage.
- **Late ratings** (someone rates a brewery after the day): put them in that brewery's original stop and say which stage.
- **A person already rated that stop:** this is a correction. Show old → new and get an OK.
- **Plan changes** ("Marcus first, Lemke second"): reorder the stops. Times and notes stay with their slot unless the
  user says otherwise. `note` is short text such as "Table booked for 20:00". Never store reservation numbers.
- **New season:** id is the end year, `label` is `YYYY/YYYY` (or one year). Create `seasons/<id>.json`, append the id to
  `manifest.json` (oldest first). Ask for the first stage date. The new season becomes the page's default season at once,
  so plan its first stage (below) in the same change, or visitors land on an empty season.
- **Planning the next stage:** append `{"date": "YYYY-MM-DD", "stops": [...]}` to the latest season, stops with `brewery`,
  `start`, `end`, `travel`, `note` and `"ratings": {}`. Only the date is known? Use `"stops": []`. The page then shows a
  "Next stage" banner on the front page and the Agenda tab with the date (and placeholders for missing stops). With no
  upcoming stage the Agenda tab shows "to be announced" placeholders, so never invent a plan. A stage keeps its place
  after its date; ratings then go into it as usual.

## Writing the files

1-space indent, ratings one per line like `"ines": {"beer": 4, "service": 3, "gl": 3}`, keep people in the order they
already have in the stop, end with a newline. Change nothing you were not asked to change. In chat, return the whole file.

## Git (code tools only)

Pushing is allowed because the user wants to update from a phone. A push goes live on GitHub Pages within about a
minute, so:

- Push only when `validate.py` passes on the whole `data/` folder **and** the user said OK to exactly this change.
- Only commit files under `data/`. Never touch `index.html`, `.claude/` or anything else in this workflow.
- `validate.py` also checks that `index.html` has an empty data block. Never push if it reports embedded test data.
- One commit per stop or correction, message like `2026: add Lemke ratings (7)`. Push the current branch only.
- If the push is rejected, stop and tell the user. **Never force push**, rewrite history or push to another branch.
- Undo = `git revert` of the last commit as a new commit, then validate and push. Never reset.
- After pushing, say the commit id and that the page updates in about a minute.

## Never

- Invent a person, brewery, score or date. Guess a digit you cannot read. Store averages, ranks or halves.
- Open old seasons without a reason. Edit `index.html`. Push without an OK or without a passing validation.
