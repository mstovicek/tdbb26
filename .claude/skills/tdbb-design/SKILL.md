---
name: tdbb-design
description: Change or redesign the TDBB results page (index.html), including layout, style, new views and loader code. Never edits data files; use tdbb-ingest for ratings.
---

# TDBB design

Edits `index.html`, the single-file, mobile-first results page. Data lives in `data/` and is handled by the
`tdbb-ingest` skill. Keep the two apart: a redesign never touches ratings, and rating updates never touch the page.

## How the page is built

One file, no libraries, no build step. Inside the `<script>`:

1. **Loading** (`loadData`, `showFatal`). If `<script type="application/json" id="tdbb-data">` has content, that
   embedded data is used and a "Test data" banner shows. Otherwise it fetches `data/manifest.json`, `people.json`,
   `breweries.json` and each `data/seasons/<id>.json`, with a cache-busting query and `cache: 'no-store'`.
   A season that fails to load or parse becomes a banner; the rest keeps working. Missing manifest, people or
   breweries shows a plain error. Opening the file straight from disk explains that fetching is blocked.
2. **Model** (`buildModel`, `entries`, `pickAgenda`). Turns the files into `STAGES`, `PEOPLE`, `BREWERIES`
   (each with a `ratings` list of `{p, v:[beer,service,gl], st, sid}`), `PROFILES`, `AGENDA` and `SCOPE`.
   One season selected: breweries are that season's stops. **All**: breweries are pooled, "stages" become seasons.
   Bad rows (unknown id, score not an integer 0 to 5) are skipped with a warning banner.
3. **Calculations** (`computeBrews`, `computePeople`). All averages, ranks, deviations and favourites are worked out
   here from the ratings. Weights come from `manifest.json`. Nothing derived is ever stored in the data.
4. **Views.** `renderWinners`, `renderProfiles` (Breweries), `renderTour` → `renderBreweries` (Ratings) and
   `renderToday`, `renderPeople` → Scores, Favourites, Attendance, Consistency.
5. **Shell.** `render()`, hash routing (`#winners`, `#breweries`, `#tour-ratings`, `#tour-today`,
   `#people-<tab>`), one delegated click handler, the year selector in the header.

Header: logo, rated count, season selector. Bottom menu: Winners, Breweries, Tour, People.

## The data contract

The loader and model read exactly the format in `../tdbb-ingest/references/format.md`. Do not change what a field means
or rename one as part of a design task. If the format must change, treat it as its own task: update the validator,
`format.md`, the ingest skill, the loader and migrate every data file together, then run all checks.

## Guardrails

- **Never commit embedded data in `index.html`.** The live page keeps its `tdbb-data` block empty so it always reads
  the real files. Test builds go to `index-test.html` (git-ignored).
- Never edit anything under `data/`. Never put sample or fake ratings in the repo.
- Keep working: empty states (no ratings, no seasons), one season and many seasons, All and a single season,
  long brewery names, people with few ratings, a closed brewery, a stage without times.
- Keep the page one file, with no remote images and no remote scripts. Fonts: Barlow from Google Fonts with a system
  fallback. Photos are `img/<breweryid>.jpg`, shown as a circle over an initials fallback.
- Mobile first: check at 360 and 390 px wide, no sideways scrolling, tap targets at least 38 px, text at least 12 px.
- External links open in a new window (already handled by the click handler for `a[target="_blank"]`).
- Typographic punctuation in visible text: ’ for apostrophes, real minus sign, en dash in time ranges.

## Visual language

Dark charcoal `#353433` background, raised `#403f3d`, lines `#504e4b`, text `#F5EFE4`, muted `#ABA69C`, gold `#E7C566`
(highlights, best values), lilac `#BBA9FF` (lowest values), purple `#7456E0` (rank circles, stop numbers), cream `#FBEBD3`
(active chips, primary buttons, dark ink `#2B2A29` on it). The TDBB wordmark is heavy gold type with a dark extruded shadow.
Rank circles echo the Tour screen from the original TDP app design. Keep tables simple and sortable, one screenful per section.

## Testing a change

1. Check the data first: `python3 .claude/skills/tdbb-ingest/scripts/validate.py data`.
2. Real loading path: serve the repo root (`python3 -m http.server 8000`) and open `http://localhost:8000/`.
3. Embedded path (also works in previews that cannot fetch):
   `python3 .claude/skills/tdbb-design/scripts/embed.py` writes `index-test.html` and refuses to overwrite `index.html`.
4. Compare numbers before and after a redesign: rankings, people tables and the Winners podium must not change
   unless the change was meant to alter them.
5. Before handing over, confirm `index.html` still has an empty `tdbb-data` block (the validator checks this).
