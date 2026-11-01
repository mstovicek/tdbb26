#!/usr/bin/env python3
"""Print the ranking of one season, so nobody has to do the maths by hand.

Usage:
  python3 summary.py [DATA_DIR] [SEASON_ID] [--stop BREWERY_ID]

SEASON_ID defaults to the latest season in manifest.json. With --stop, only that
brewery's line is printed (useful right after adding a stop).
Weights come from manifest.json. Standard library only.

All maths is exact (fractions), so ties are real ties and scores are rounded half up to two decimals
(3.675 prints as 3.68), the same as the page.
"""
import json, os, sys
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction


def two(x):
    """Round a Fraction half up to two decimal places and return it as text."""
    d = Decimal(x.numerator) / Decimal(x.denominator)
    return str(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def main(argv):
    args = argv[1:]
    data, sid, stop = 'data', None, None
    pos = []
    while args:
        a = args.pop(0)
        if a == '--stop' and args:
            stop = args.pop(0)
        else:
            pos.append(a)
    if pos:
        data = pos[0]
    if len(pos) > 1:
        sid = pos[1]
    load = lambda p: json.load(open(os.path.join(data, p), encoding='utf-8'))
    man = load('manifest.json')
    w = {k: Fraction(str(v)) for k, v in man['weights'].items()}
    sid = sid or man['seasons'][-1]
    season = load('seasons/%s.json' % sid)
    names = load('breweries.json')['breweries']
    rows = []
    for st in season['stages']:
        for sp in st['stops']:
            rs = list(sp['ratings'].values())
            if not rs:
                rows.append((None, sp['brewery'], 0, None))
                continue
            m = {k: Fraction(sum(r[k] for r in rs), len(rs)) for k in ('beer', 'service', 'gl')}
            overall = sum(w[k] * m[k] for k in m)
            rows.append((overall, sp['brewery'], len(rs), m))
    rated = sorted([r for r in rows if r[0] is not None], key=lambda r: -r[0])
    rank, prev = {}, None
    for i, r in enumerate(rated, 1):
        if prev is None or r[0] != prev:
            cur = i
            prev = r[0]
        rank[r[1]] = cur
    print('Season %s (%s): %d of %d stops rated' % (sid, season['label'], len(rated), len(rows)))
    for r in rated:
        if stop and r[1] != stop:
            continue
        m = r[3]
        print('%2d. %-26s overall %s  beer %s  service %s  gl %s  (%d ratings)' % (
            rank[r[1]], names[r[1]]['name'], two(r[0]), two(m['beer']), two(m['service']), two(m['gl']), r[2]))
    if not stop:
        for r in rows:
            if r[0] is None:
                print(' -. %-26s not rated yet' % names[r[1]]['name'])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
