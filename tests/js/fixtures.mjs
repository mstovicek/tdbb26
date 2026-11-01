// Test data, built in code so no fake ratings ever sit in data/. Scores are written as 'beer service gl' digits.
const r = s => ({ beer: +s[0], service: +s[1], gl: +s[2] });
const ratings = obj => Object.fromEntries(Object.entries(obj).map(([p, s]) => [p, r(s)]));
const place = (name, extra = {}) => ({ name, address: name + ' Street 1, 10115 Berlin', highlight: 'A place.', status: 'open', ...extra });

export const WEIGHTS = { beer: 0.5, service: 0.25, gl: 0.25 };

/**
 * alpha  open, brews on site, district Mitte          2025 3.00  2026 4.17   (improved)
 * beta   open, does NOT brew on site (Kreuzberg)      2025 2.00  2026 5.00   (improved most, but does not qualify)
 * gamma  CLOSED but brewed on site, no district       2025 5.00  2026 5.00
 * delta  open, brews on site (Friedrichshain)         2025 4.50  2026 3.00   (got worse)
 * eps    open, brews on site (Neukölln)               2026 only, 3.875
 */
export function mainBundle() {
  return {
    manifest: { version: 1, weights: WEIGHTS, seasons: ['2025', '2026'] },
    people: { version: 1, people: { ines: { name: 'Ines' }, milan: { name: 'Milan' }, tim: { name: 'Tim' }, ola: { name: 'Ola' } } },
    breweries: { version: 1, breweries: {
      alpha: place('Alpha', { district: 'Mitte' }),
      beta: place('Beta', { district: 'Kreuzberg', brewsOnSite: false }),
      gamma: place('Gamma', { status: 'closed' }),
      delta: place('Delta', { district: 'Friedrichshain' }),
      eps: place('Eps', { district: 'Neukölln' }),
    } },
    seasons: {
      2025: { version: 1, id: '2025', label: '2024/2025', stages: [{ date: '2025-05-10', stops: [
        { brewery: 'alpha', ratings: ratings({ ines: '333', milan: '333', tim: '333' }) },
        { brewery: 'beta', ratings: ratings({ ines: '222' }) },
        { brewery: 'gamma', ratings: ratings({ ines: '555' }) },
        { brewery: 'delta', ratings: ratings({ ines: '544', milan: '544', tim: '544' }) },
      ] }] },
      2026: { version: 1, id: '2026', label: '2025/2026', stages: [
        { date: '2026-04-10', stops: [
          { brewery: 'alpha', start: '14:00', ratings: ratings({ ines: '544', milan: '444', tim: '444' }) },
          { brewery: 'beta', ratings: ratings({ ines: '555' }) },
          { brewery: 'gamma', ratings: ratings({ ines: '555' }) },
          { brewery: 'delta', ratings: ratings({ ines: '333' }) },
        ] },
        { date: '2026-05-15', stops: [
          { brewery: 'eps', ratings: ratings({ ines: '444', milan: '444', tim: '444', ola: '433' }) },
        ] },
      ] },
    },
  };
}

/** A copy of the bundle with one more stage on the latest season. */
export function withStage(bundle, stage) {
  const b = structuredClone(bundle);
  b.seasons['2026'].stages.push(stage);
  return b;
}

/**
 * Seven people who rated 6, 5, 4, 3, 3, 2 and 1 breweries, for the "regulars" list:
 * p1 6, p2 5, p3 4, p4 3, p5 3 (tied with p4), p6 2, p7 1 (does not fit in five places).
 */
export function regularsBundle() {
  const names = ['Ann', 'Bob', 'Cid', 'Dee', 'Eve', 'Fay', 'Gus'];
  const people = Object.fromEntries(names.map((n, i) => ['p' + (i + 1), { name: n }]));
  const breweries = Object.fromEntries([1, 2, 3, 4, 5, 6].map(i => ['b' + i, place('B' + i)]));
  const counts = [6, 5, 4, 3, 3, 2, 1];
  const stops = [1, 2, 3, 4, 5, 6].map(i => ({
    brewery: 'b' + i,
    ratings: ratings(Object.fromEntries(counts.map((c, pi) => [pi, c]).filter(([pi, c]) => i <= c).map(([pi]) => ['p' + (pi + 1), '333']))),
  }));
  return {
    manifest: { version: 1, weights: WEIGHTS, seasons: ['2026'] }, people: { version: 1, people },
    breweries: { version: 1, breweries },
    seasons: { 2026: { version: 1, id: '2026', label: '2025/2026', stages: [{ date: '2026-04-10', stops }] } },
  };
}

/**
 * For the voting twins. Six breweries, one stage, every brewery rated by everyone except Zed (who rated only b1 and b2).
 *   Ann = Ben = base1, Cat = base1 with one score 1 point off   -> a trio, 0.04 apart
 *   Dan = base2, Eve = base2 with 3 points off                  -> a pair, 0.17 apart
 *   Fay = base3, Gus = base3 with 5 points off                  -> a pair, 0.28 apart
 *   Hal rates everything 0; Zed copies Ann but only has 2 breweries in common with anyone.
 */
const BASE1 = ['333', '424', '543', '222', '445', '351'];
const BASE2 = ['155', '240', '012', '554', '110', '205'];
const BASE3 = ['501', '052', '335', '100', '522', '033'];
const tweak = (base, changes) => base.map((s, i) => { const d = s.split('').map(Number); (changes[i] || []).forEach(([c, by]) => { d[c] += by; }); return d.join(''); });
export const TWIN_SCORES = {
  Ann: BASE1, Ben: BASE1, Cat: tweak(BASE1, { 0: [[0, 1]] }),
  Dan: BASE2, Eve: tweak(BASE2, { 1: [[1, -1]], 3: [[2, -1]], 5: [[0, 1]] }),
  Fay: BASE3, Gus: tweak(BASE3, { 0: [[0, -1]], 1: [[2, -2]], 2: [[1, -1]], 4: [[0, -1]] }),
  Hal: Array(6).fill('000'),
};

export function twinsBundle(scores = TWIN_SCORES) {
  const all = { ...scores, Zed: BASE1.slice(0, 2) };
  const people = Object.fromEntries(Object.keys(all).map(n => [n.toLowerCase(), { name: n }]));
  const breweries = Object.fromEntries([1, 2, 3, 4, 5, 6].map(i => ['b' + i, place('B' + i)]));
  const stops = [0, 1, 2, 3, 4, 5].map(i => ({
    brewery: 'b' + (i + 1),
    ratings: ratings(Object.fromEntries(Object.entries(all).filter(([, v]) => v[i] !== undefined).map(([n, v]) => [n.toLowerCase(), v[i]]))),
  }));
  return {
    manifest: { version: 1, weights: WEIGHTS, seasons: ['2026'] }, people: { version: 1, people }, breweries: { version: 1, breweries },
    seasons: { 2026: { version: 1, id: '2026', label: '2025/2026', stages: [{ date: '2026-04-10', stops }] } },
  };
}

/** Two people who share b1 in two seasons and b2 in one: 3 visits on All, 1 in 2026 alone, 2 in 2025 alone. */
export function twoSeasonPairBundle() {
  const b = twinsBundle({ Xan: ['333', '333'], Yui: ['333', '333'] });
  b.manifest.seasons = ['2025', '2026'];
  const mk = (sid, label, date, stops) => ({ version: 1, id: sid, label, stages: [{ date, stops }] });
  const rate = n => ratings({ xan: n, yui: n });
  b.seasons = {
    2025: mk('2025', '2024/2025', '2025-05-10', [{ brewery: 'b1', ratings: rate('333') }, { brewery: 'b2', ratings: rate('333') }]),
    2026: mk('2026', '2025/2026', '2026-04-10', [{ brewery: 'b1', ratings: rate('333') }]),
  };
  b.people.people = { xan: { name: 'Xan' }, yui: { name: 'Yui' } };
  return b;
}

/**
 * For the twins per category. Each person follows one of six very different score patterns per category:
 *   beer: Ann = Ben (identical)   service: Cat = Dan (identical)   GL: Eve = Fay (identical)
 * so each category has its own perfect pair, while overall nobody is that close. Xan and Yui are identical on
 * everything but only share 3 breweries: enough for the overall view (3), not for a single category (4).
 */
const PATTERN = [[0, 0, 0, 0, 0, 0], [0, 1, 2, 3, 4, 5], [0, 2, 4, 0, 2, 4], [0, 3, 0, 3, 0, 3], [0, 4, 2, 0, 4, 2], [0, 5, 4, 3, 2, 1]];
const WHICH = { Ann: [1, 0, 0], Ben: [1, 2, 2], Cat: [0, 1, 3], Dan: [2, 1, 5], Eve: [3, 3, 1], Fay: [5, 5, 1] };   // [beer, service, GL] pattern per person
export function categoryTwinsBundle() {
  const scores = Object.fromEntries(Object.entries(WHICH).map(([n, w]) => [n, [0, 1, 2, 3, 4, 5].map(i => w.map(p => PATTERN[p][i]).join(''))]));
  scores.Xan = scores.Yui = [0, 1, 2].map(i => String(PATTERN[4][i]).repeat(3));
  return twinsBundle(scores);
}
