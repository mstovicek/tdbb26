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
   `PROFILES[id]` carries `qual` (`brewsOnSite` is not `false`) and `elig` (`qual` and `status` open). `buildHistory`
   fills `HISTORY[id]`: each brewery's overall score per season it was rated, **whatever season is selected**, so
   trends work in every view.
3. **Calculations** (`computeBrews`, `computePeople`). All averages, ranks, deviations and favourites are worked out
   here from the ratings. Weights come from `manifest.json`. Nothing derived is ever stored in the data.
   Trends are derived too: `sparkline` (last season against the one before it) and `movers`
   (biggest improvements of the selected season, or the latest on All, against each brewery's previous rated season).
4. **Views.** `renderWinners` (a **Next stage** banner when the latest season has a stage today or later, linking to the Agenda;
   podium of the three best breweries, **Biggest movers**, top five regulars),
   `renderProfiles` (Breweries: sort Top rated or A to Z; district shown before the address; a sparkline per brewery rated in
   two or more seasons, **only when Season = All**;
   badges Closed and Doesn't qualify), `renderTour` → `renderBreweries` (Ratings) and
   `renderAgenda` (placeholders when nothing is planned), `renderPeople` → Attendance, Scores, Favourites, Consistency.
5. **Shell.** `render()`, hash routing (`#winners`, `#breweries`, `#tour-ratings`, `#tour-agenda` (the old `#tour-today` still works),
   `#people-<tab>`), one delegated click handler, the year selector in the header. The selected season is kept in the
   query string (`?year=2025` or `?year=all`, set with `history.replaceState`) so a refresh keeps it; the view stays in the hash.

Header: logo, rated count, season selector. The logo is inline SVG text in Bungee (loaded for those four letters only; the font has one weight, so never set
font-weight on it): dark faces with a thin muted-gold outline and inline, and a solid gold extrusion falling down-left,
built from layered `<use>` copies and a clip path. It follows the TDP logo screenshot.
The Winners page has no trophy icon, to save space.

Bottom menu: Winners, Breweries, Tour, People.

## Qualification

A brewery **qualifies** for the tour while it still brews on site (`brewsOnSite` is not `false`). Being closed is a
separate thing: a closed brewery that brewed on site still qualifies and only gets the Closed badge. The all-time Winners
podium (on All) and Biggest movers leave out breweries that are closed or do not qualify (`elig`); every season
ranking keeps them. The rule lives in the page; the data only holds the two facts. The Winners intro explains it, with
"brewing on site" highlighted.

## The data contract

The loader and model read exactly the format in `../tdbb-ingest/references/format.md`. Do not change what a field means
or rename one as part of a design task. If the format must change, treat it as its own task: update the validator,
`format.md`, the ingest skill, the loader and migrate every data file together, then run all checks.

## Guardrails

- **Never commit embedded data in `index.html`.** The live page keeps its `tdbb-data` block empty so it always reads
  the real files. Test builds go to `index-test.html` (git-ignored).
- Never edit anything under `data/`. Never put sample or fake ratings in the repo; test data is built inside the tests
  (`tests/js/fixtures.mjs`), never stored as files.
- Keep working: empty states (no ratings, no seasons), one season and many seasons, All and a single season,
  long brewery names, people with few ratings, a closed brewery, a stage without times, no upcoming stage (Agenda
  placeholders, no banner), a planned stage with a date but no stops (empty stages are not listed under Ratings).
- Do not hardcode brewery names, ids, seasons or scores in the page, and keep state words (closed, no longer qualifies)
  out of data text: the page shows badges from the fields.
- The favicon is an inline SVG data URI in `<head>` (gold beer mug on charcoal), so it needs no extra file.
- Keep the page one file, with no remote images and no remote scripts. Fonts: Barlow from Google Fonts with a system
  fallback. Photos are `img/<breweryid>.jpg`, shown as a circle over an initials fallback. Use only the group's own photos
  (or with permission); never copy from Google Maps. There are none for now, so every brewery shows initials.
- Mobile first: check at 360 and 390 px wide, no sideways scrolling, tap targets at least 38 px, text at least 12 px.
- External links open in a new window (already handled by the click handler for `a[target="_blank"]`).
- Typographic punctuation in visible text: ’ for apostrophes, real minus sign, en dash in time ranges.

## Visual language

Dark charcoal `#353433` background, raised `#403f3d`, lines `#504e4b`, text `#F5EFE4`, muted `#ABA69C`, gold `#E7C566`
(highlights, best values), lilac `#BBA9FF` (lowest values), purple `#7456E0` (rank circles, stop numbers), cream `#FBEBD3`
(active chips, primary buttons, dark ink `#2B2A29` on it). The TDBB wordmark has dark faces with thin muted-gold lines and a solid gold extrusion down-left, after the TDP logo.
The Next stage banner is a gold-outlined card on a faint gold tint; placeholder stops use dashed circles and muted text.
Rank circles echo the Tour screen from the original TDP app design. Keep tables simple and sortable, one screenful per section.

## Testing a change

0. Run the tests: `node --test tests/js/` (page) and `python3 -m unittest discover -s tests/python` (scripts and the
   Python/JS cross-check). A change that alters a number, a rank or a rule should come with a test. The page tests use
   `tests/js/harness.mjs`, which runs the real script against a browser stand-in; if the page starts using a new browser
   feature, add it to the stand-in or the page will quietly fall back (that is how `URLSearchParams` was once missed).
1. Check the data first: `python3 .claude/skills/tdbb-ingest/scripts/validate.py data`.
2. Real loading path: serve the repo root (`python3 -m http.server 8000`) and open `http://localhost:8000/`.
3. Embedded path (also works in previews that cannot fetch):
   `python3 .claude/skills/tdbb-design/scripts/embed.py` writes `index-test.html` and refuses to overwrite `index.html`.
4. Compare numbers before and after a redesign: rankings, people tables and the Winners podium must not change
   unless the change was meant to alter them.
5. For the front-page banner and an Agenda with a plan, use `embed.py --test-agenda`: it adds an invented stage 14 days
   ahead to the embedded copy only (never to `data/`).
6. Look at it in a real browser at 390 px wide, not only through scripts: that is how a faked bold font and clogged
   letters in the logo were caught. Zoom in on details such as the logo.
7. Before handing over, confirm `index.html` still has an empty `tdbb-data` block (the validator checks this).
