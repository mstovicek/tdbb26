"""Cross-check: summary.py (Python) and the page (JavaScript) must print the same ranks and scores.

Both compute the scores on their own. This runs the same data through both and compares every number as text,
so a rounding difference (such as 3.675 showing as 3.67 in one and 3.68 in the other) fails the test.
Needs Node.js; the test is skipped when it is not installed.
"""
import json, os, random, re, shutil, subprocess, unittest
from helpers import ROOT, SUMMARY, TempCase, base_data, brewery, run, score, write_data

NODE = shutil.which('node')
DUMP = os.path.join(ROOT, 'tests', 'js', 'dump_ratings.mjs')
LINE = re.compile(r'^\s*(\d+)\. (.+?)\s{2,}overall (\S+)  beer (\S+)  service (\S+)  gl (\S+)  \((\d+) ratings?\)$')


def pid(i):
    return 'p' + chr(97 + i // 26) + chr(97 + i % 26)


def tricky_data(seed=7):
    """Random ratings plus hand-made awkward cases: exact half cents, repeating decimals, ties."""
    rnd = random.Random(seed)
    people = {pid(i): {'name': 'Person %d' % i} for i in range(14)}
    per = {}
    for n in range(30):
        per['rand%02d' % n] = [(rnd.randint(0, 5), rnd.randint(0, 5), rnd.randint(0, 5)) for _ in range(rnd.randint(1, 12))]
    per['halfcent'] = [(4, 4, 4), (5, 4, 5), (4, 4, 4), (5, 3, 4), (3, 4, 5), (4, 4, 4), (3, 4, 2), (4, 2, 4), (3, 3, 3), (3, 2, 2)]   # exactly 3.675
    per['half2'] = [(4, 4, 4), (4, 4, 4), (4, 4, 4), (5, 3, 3)]                    # beer 4.25 service 3.75 gl 3.75 -> 4.0
    per['third'] = [(4, 4, 4), (4, 4, 4), (3, 3, 3)]                               # repeating 3.666...
    per['twin1'] = per['twin2'] = [(3, 3, 3), (4, 2, 5)]                           # a tie
    per['zeros'] = [(0, 0, 0)]
    per['fives'] = [(5, 5, 5)] * 3
    d = base_data()
    d['people']['people'] = people
    d['breweries']['breweries'] = {b: brewery(b.title()) for b in per}
    stops = [{'brewery': b, 'ratings': {pid(i): score(*s) for i, s in enumerate(rows)}} for b, rows in per.items()]
    third = len(stops) // 3 + 1
    d['seasons']['2026']['stages'] = [
        {'date': '2026-04-%02d' % (10 + i), 'stops': stops[i * third:(i + 1) * third]} for i in range(3) if stops[i * third:(i + 1) * third]]
    return d


@unittest.skipUnless(NODE, 'Node.js is not installed')
class CrossCheckTests(TempCase):
    def python_rows(self, data):
        code, out = run(SUMMARY, data, '2026')
        self.assertEqual(code, 0, out)
        rows = {}
        for line in out.splitlines():
            m = LINE.match(line)
            if m:
                rows[m.group(2)] = dict(rank=m.group(1), overall=m.group(3), beer=m.group(4), service=m.group(5), gl=m.group(6))
        return rows

    def page_rows(self, data):
        p = subprocess.run([NODE, DUMP, data, '2026'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return {r['name']: dict(rank=r['rank'], overall=r['overall'], beer=r['beer'], service=r['service'], gl=r['gl'])
                for r in json.loads(p.stdout)}

    def test_summary_and_page_agree_on_every_number(self):
        data = write_data(self.tmp, tricky_data())
        py, js = self.python_rows(data), self.page_rows(data)
        self.assertGreater(len(py), 30)
        self.assertEqual(sorted(py), sorted(js), 'both must list the same breweries')
        mismatches = ['%s: summary.py %s, page %s' % (name, py[name], js[name]) for name in sorted(py) if py[name] != js[name]]
        self.assertEqual(mismatches, [], '\n'.join(mismatches))

    def test_the_awkward_cases_are_what_we_expect(self):
        data = write_data(self.tmp, tricky_data())
        for rows in (self.python_rows(data), self.page_rows(data)):
            self.assertEqual(rows['Halfcent']['overall'], '3.68')      # 3.675 rounds up
            self.assertEqual(rows['Third']['overall'], '3.67')
            self.assertEqual(rows['Twin1']['rank'], rows['Twin2']['rank'])
            self.assertEqual(rows['Fives']['overall'], '5.00')
            self.assertEqual(rows['Zeros']['overall'], '0.00')

    def test_other_random_data_sets_also_agree(self):
        for seed in (1, 2, 3, 4, 5):
            with self.subTest(seed=seed):
                data = write_data(self.tmp, tricky_data(seed))
                self.assertEqual(self.python_rows(data), self.page_rows(data))


if __name__ == '__main__':
    unittest.main()
