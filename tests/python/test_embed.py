import json, os, re, unittest
from datetime import datetime, timedelta
from helpers import TempCase, EMBED, base_data, brewery, read, run, write, write_data

TEMPLATE = '<html><body><script type="application/json" id="tdbb-data"></script><script>// page</script></body></html>'


class EmbedTests(TempCase):
    def setUp(self):
        super().setUp()
        self.template = os.path.join(self.tmp, 'tpl.html')
        write(self.template, TEMPLATE)
        self.out = os.path.join(self.tmp, 'index-test.html')

    def build(self, *extra, data=None, out=None):
        data = data or self.data()
        return run(EMBED, '--data', data, '--template', self.template, '--out', out or self.out, *extra, cwd=self.tmp)

    def payload(self, path=None):
        html = read(path or self.out)
        m = re.search(r'<script[^>]*id="tdbb-data"[^>]*>(.*?)</script>', html, re.S)
        return json.loads(m.group(1).replace('<\\/', '</'))

    def test_embeds_all_the_data(self):
        code, out = self.build()
        self.assertEqual(code, 0, out)
        p = self.payload()
        self.assertEqual(sorted(p), ['breweries', 'builtAt', 'manifest', 'people', 'seasons'])
        self.assertEqual(list(p['seasons']), ['2026'])
        self.assertIn('alpha', p['breweries']['breweries'])

    def test_the_template_is_not_changed(self):
        self.build()
        self.assertEqual(read(self.template), TEMPLATE)

    def test_refuses_to_overwrite_index_html(self):
        code, out = self.build(out=os.path.join(self.tmp, 'index.html'))
        self.assertEqual(code, 1)
        self.assertIn('refusing to write index.html', out)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, 'index.html')))

    def test_refuses_to_overwrite_its_template(self):
        code, out = self.build(out=self.template)
        self.assertEqual(code, 1)
        self.assertEqual(read(self.template), TEMPLATE)

    def test_invalid_data_builds_nothing(self):
        def bad(d):
            d['seasons']['2026']['stages'][0]['stops'][0]['ratings']['tim'] = {'beer': 9, 'service': 3, 'gl': 3}
        code, out = self.build(data=self.data(bad))
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(self.out))

    def test_template_without_a_data_block_fails(self):
        write(self.template, '<html></html>')
        code, out = self.build()
        self.assertEqual(code, 1)
        self.assertIn('tdbb-data', out)

    def test_closing_script_tags_in_data_cannot_break_the_page(self):
        def m(d):
            d['breweries']['breweries']['alpha']['highlight'] = 'x </script><b>y'
        code, out = self.build(data=self.data(m))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.payload()['breweries']['breweries']['alpha']['highlight'], 'x </script><b>y')

    # ---- --test-agenda
    def many_breweries(self, d):
        for i, n in enumerate(('delta', 'epsilon', 'zeta')):
            d['breweries']['breweries'][n] = brewery(n.title())
            d['seasons']['2026']['stages'][1]['stops'].append({'brewery': n, 'ratings': {}})

    def test_test_agenda_adds_an_upcoming_stage_to_the_output_only(self):
        data = self.data(self.many_breweries)
        before = {f: read(os.path.join(data, 'seasons', f)) for f in os.listdir(os.path.join(data, 'seasons'))}
        code, out = self.build('--test-agenda', data=data)
        self.assertEqual(code, 0, out)
        stages = self.payload()['seasons']['2026']['stages']
        self.assertEqual(len(stages), 3)
        last = stages[-1]
        self.assertEqual(last['date'], (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'))
        self.assertEqual(len(last['stops']), 4)
        self.assertTrue(all(s['ratings'] == {} for s in last['stops']))
        self.assertIn('Test agenda', last['stops'][0]['note'])
        after = {f: read(os.path.join(data, 'seasons', f)) for f in os.listdir(os.path.join(data, 'seasons'))}
        self.assertEqual(before, after, 'the real data files must never change')

    def test_test_agenda_skips_closed_and_non_brewing_breweries(self):
        def m(d):
            self.many_breweries(d)
            d['breweries']['breweries']['alpha']['status'] = 'closed'
            d['breweries']['breweries']['beta']['brewsOnSite'] = False
        code, out = self.build('--test-agenda', data=self.data(m))
        self.assertEqual(code, 0, out)
        used = [s['brewery'] for s in self.payload()['seasons']['2026']['stages'][-1]['stops']]
        self.assertNotIn('alpha', used)
        self.assertNotIn('beta', used)

    def test_without_the_flag_no_stage_is_added(self):
        self.build()
        self.assertEqual(len(self.payload()['seasons']['2026']['stages']), 2)

    def test_test_agenda_needs_at_least_one_open_brewery(self):
        def m(d):
            for b in d['breweries']['breweries'].values():
                b['status'] = 'closed'
        code, out = self.build('--test-agenda', data=self.data(m))
        self.assertEqual(code, 1)
        self.assertIn('nothing to build', out)

    def test_unknown_argument_fails(self):
        code, out = self.build('--nope')
        self.assertEqual(code, 1)


if __name__ == '__main__':
    unittest.main()
