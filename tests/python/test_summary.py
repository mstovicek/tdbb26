import json, os, unittest
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from helpers import TempCase, SUMMARY, base_data, brewery, run, score, write_data


def season_data(per_brewery, weights=None):
    """per_brewery: {id: [(beer, service, gl), ...]}. Each rating gets its own person."""
    d = base_data()
    people, breweries, stops = {}, {}, []
    for bid, rows in per_brewery.items():
        breweries[bid] = brewery(bid.title())
        ratings = {}
        for i, (b, s, g) in enumerate(rows):
            pid = 'p' + chr(97 + i // 26) + chr(97 + i % 26)
            people[pid] = {'name': pid.title()}
            ratings[pid] = score(b, s, g)
        stops.append({'brewery': bid, 'ratings': ratings})
    d['people']['people'] = people
    d['breweries']['breweries'] = breweries
    d['seasons']['2026']['stages'] = [{'date': '2026-05-01', 'stops': stops}]
    if weights:
        d['manifest']['weights'] = weights
    return d


def half_up(frac):
    return str((Decimal(frac.numerator) / Decimal(frac.denominator)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


class SummaryTests(TempCase):
    def summary(self, per_brewery, *args, weights=None):
        data = write_data(self.tmp, season_data(per_brewery, weights))
        code, out = run(SUMMARY, data, *args)
        self.assertEqual(code, 0, out)
        return out

    def test_the_half_cent_rounds_up(self):
        # beer 38/10, service 34/10, gl 37/10 gives exactly 3.675, which must print as 3.68
        rows = [(4, 4, 4), (5, 4, 5), (4, 4, 4), (5, 3, 4), (3, 4, 5), (4, 4, 4), (3, 4, 2), (4, 2, 4), (3, 3, 3), (3, 2, 2)]
        out = self.summary({'tied': rows})
        self.assertIn('overall 3.68  beer 3.80  service 3.40  gl 3.70  (10 ratings)', out)

    def test_repeating_decimals_round_normally(self):
        out = self.summary({'third': [(4, 4, 4), (4, 4, 4), (3, 3, 3)]})   # averages are 3.666...
        self.assertIn('overall 3.67  beer 3.67  service 3.67  gl 3.67', out)

    def test_exact_values_are_not_changed(self):
        out = self.summary({'exact': [(5, 5, 5), (3, 3, 3)]})
        self.assertIn('overall 4.00  beer 4.00  service 4.00  gl 4.00', out)

    def test_ranking_is_best_first_with_shared_places(self):
        out = self.summary({'low': [(2, 2, 2)], 'high': [(5, 5, 5)], 'twin1': [(3, 3, 3)], 'twin2': [(3, 3, 3)]})
        lines = [l for l in out.splitlines() if l[:2].strip().rstrip('.').isdigit()]
        names = [l.split()[1] for l in lines]
        ranks = [l.split('.')[0].strip() for l in lines]
        self.assertEqual(names, ['High', 'Twin1', 'Twin2', 'Low'])
        self.assertEqual(ranks, ['1', '2', '2', '4'])

    def test_almost_equal_scores_are_not_a_tie(self):
        # 4.005 vs 4.00: different exact values must keep different ranks even though both could print alike
        a = [(4, 4, 4)] * 199 + [(5, 4, 4)]      # beer slightly above 4
        b = [(4, 4, 4)] * 200
        out = self.summary({'a': a, 'b': b})
        self.assertRegex(out, r' 1\. A ')
        self.assertRegex(out, r' 2\. B ')

    def test_unrated_stops_are_listed_apart(self):
        out = self.summary({'rated': [(3, 3, 3)], 'empty': []})
        self.assertIn('1 of 2 stops rated', out)
        self.assertIn('-. Empty', out)
        self.assertIn('not rated yet', out)

    def test_stop_option_prints_one_brewery_only(self):
        out = self.summary({'one': [(3, 3, 3)], 'two': [(4, 4, 4)]}, '--stop', 'one')
        self.assertIn('One', out)
        self.assertNotIn('Two', out)
        self.assertIn('2. One', out.replace('  ', ' ').replace(' 2. ', ' 2. '))   # rank is still the season rank

    def test_weights_come_from_the_manifest(self):
        out = self.summary({'x': [(5, 1, 1)]}, weights={'beer': 1, 'service': 0, 'gl': 0})
        self.assertIn('overall 5.00', out)

    def test_every_value_matches_an_independent_calculation(self):
        rows = {'a': [(3, 5, 2), (4, 1, 4), (2, 2, 5)], 'b': [(5, 5, 4), (1, 3, 3)], 'c': [(0, 0, 1)] * 7}
        out = self.summary(rows)
        w = {'beer': Fraction(1, 2), 'service': Fraction(1, 4), 'gl': Fraction(1, 4)}
        for bid, rs in rows.items():
            m = {k: Fraction(sum(r[i] for r in rs), len(rs)) for i, k in enumerate(('beer', 'service', 'gl'))}
            overall = sum(w[k] * m[k] for k in m)
            expect = 'overall %s  beer %s  service %s  gl %s' % (half_up(overall), half_up(m['beer']), half_up(m['service']), half_up(m['gl']))
            self.assertIn(expect, out, bid)

    def test_defaults_to_the_latest_season_and_accepts_a_season_id(self):
        d = season_data({'x': [(3, 3, 3)]})
        d['manifest']['seasons'] = ['2025', '2026']
        d['seasons']['2025'] = {'version': 1, 'id': '2025', 'label': '2024/2025', 'stages': [
            {'date': '2025-05-01', 'stops': [{'brewery': 'x', 'ratings': {'paa': score(5, 5, 5)}}]}]}
        data = write_data(self.tmp, d)
        self.assertIn('Season 2026', run(SUMMARY, data)[1])
        out = run(SUMMARY, data, '2025')[1]
        self.assertIn('Season 2025', out)
        self.assertIn('overall 5.00', out)


if __name__ == '__main__':
    unittest.main()
