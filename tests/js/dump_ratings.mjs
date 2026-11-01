// Prints the Tour > Ratings table of one season as JSON. Used by the Python cross-check test.
//   node tests/js/dump_ratings.mjs DATA_DIR SEASON_ID
import { loadBundle, ratingsRows, renderPage } from './harness.mjs';

const [dataDir, season] = process.argv.slice(2);
const { html } = await renderPage({ bundle: loadBundle(dataDir), hash: '#tour-ratings', search: '?year=' + season });
console.log(JSON.stringify(ratingsRows(html)));
