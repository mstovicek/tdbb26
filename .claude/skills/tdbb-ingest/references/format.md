# TDBB data format (version 1)

All files are UTF-8 JSON, 1-space indent, ending with a newline. Every file has `"version": 1`.
The validator (`scripts/validate.py`) enforces everything on this page.

## Files

```
data/manifest.json          which seasons exist, and the score weights
data/people.json            everyone who rates
data/breweries.json         every brewery, with address and a one-line highlight
data/seasons/<year>.json    one file per season, named by its END year
```

## IDs

- People and breweries: lowercase ASCII letters only, one word, no digits, hyphens or spaces.
- Accents become plain letters (`ü`→`ue`, `ß`→`ss`, `ä`→`ae`, `ö`→`oe`, `š`→`s`, `ď`→`d`).
- Breweries: the brand name run together, without trailing words like "Brauerei":
  `berlinerberg`, `strassenbrau`, `hopsandbarley`, `lemkehackeschermarkt`, `brlo`.
- Seasons: the year the season ends: `2025` is 2024/2025, `2026` is 2025/2026, `2027` is 2027.
- An id never changes once used. Display names can.

## manifest.json

```json
{"version": 1,
 "weights": {"beer": 0.5, "service": 0.25, "gl": 0.25},
 "seasons": ["2025", "2026"]}
```

Seasons are listed oldest first. The page selects the last one by default. Weights must add up to 1.
`gl` is "genius loci", the feel of the place.

## people.json

```json
{"version": 1, "people": {"matous": {"name": "Matouš"}, "jakub": {"name": "Jakub"}}}
```

Only `name`. There are no aliases: one person, one name.

## breweries.json

```json
{"version": 1, "breweries": {"suedstern": {
  "name": "Brauhaus Südstern",
  "address": "Hasenheide 69, 10967 Berlin",
  "highlight": "One sentence for people deciding where to go.",
  "status": "open"}}}
```

- `status` is `open` or `closed`. Closed breweries stay in every ranking and in All; the page only tags them.
- `highlight` is one sentence for the Breweries page. Do not put scores in new highlights (they go stale).
- Photos are not stored in the data. The page looks for `img/<breweryid>.jpg` and falls back to initials.

## seasons/<year>.json

```json
{"version": 1, "id": "2026", "label": "2025/2026", "stages": [
 {"date": "2026-10-31", "stops": [
  {"brewery": "lemkehackeschermarkt",
   "start": "16:00", "end": "17:00", "travel": 15,
   "ratings": {
    "ines":  {"beer": 4, "service": 3, "gl": 3},
    "milan": {"beer": 4, "service": 3, "gl": 3}}},
  {"brewery": "brlo", "start": "20:00", "note": "Table booked for 20:00", "ratings": {}}]}]}
```

- `id` must equal the file name. `label` is `YYYY/YYYY` or a single year like `2027`.
- A **stage** is one tour day: `date` is `YYYY-MM-DD`. Stages go oldest first. Stage and stop numbers are
  their position in the list, so nothing else stores order.
- A **stop** is one brewery visit. A brewery appears at most once per season.
- Optional stop fields: `start`, `end` (`HH:MM`, `end` after `start`, `end` needs `start`), `travel` (whole minutes to the
  next stop), `note` (short text). Leave out `end` for an open-ended last stop.
- `ratings` maps a person id to three whole numbers 0 to 5. Use `{}` for a planned stop with no scores yet.
  A late rating just goes into the stop it belongs to.
- Never store averages, ranks or totals. The page works them out.
- Do not store reservation numbers or other private details. The site is public.

## How the page uses it

- One season selected: the ranking is that season's. **All**: a brewery's score is the average of every rating it
  ever got, and a person's score is the average of all their ratings. Seasons with more raters weigh more.
- Overall = weights applied to the three averages.
- Today tab: the stage dated today, otherwise the next upcoming stage, otherwise the latest.
