import json, os, unittest
from helpers import TempCase, VALIDATE, run, score, write


class ValidateTests(TempCase):
    def check(self, mutate=None, ok=False, contains=None):
        data = self.data(mutate)
        code, out = run(VALIDATE, data, '--index', os.path.join(self.tmp, 'none.html'))
        self.assertEqual(code, 0 if ok else 1, out)
        if contains:
            self.assertIn(contains, out)
        return out

    def stops(self, d, stage=0):
        return d['seasons']['2026']['stages'][stage]['stops']

    # ---- the happy path
    def test_valid_data_passes(self):
        out = self.check(ok=True)
        self.assertIn('OK: 1 season(s), 3 people, 3 breweries, 3 ratings.', out)

    def test_planned_stage_with_no_stops_is_allowed(self):
        self.check(lambda d: d['seasons']['2026']['stages'].append({'date': '2026-07-01', 'stops': []}), ok=True)

    def test_district_and_brews_on_site_are_accepted(self):
        def m(d):
            d['breweries']['breweries']['alpha'].update(district='Mitte', brewsOnSite=False)
        self.check(m, ok=True)

    # ---- scores
    def test_score_above_five_fails(self):
        self.check(lambda d: self.stops(d)[0]['ratings'].update(tim=score(6, 3, 3)), contains='whole number from 0 to 5')

    def test_negative_score_fails(self):
        self.check(lambda d: self.stops(d)[0]['ratings'].update(tim=score(-1, 3, 3)), contains='whole number from 0 to 5')

    def test_half_score_fails(self):
        self.check(lambda d: self.stops(d)[0]['ratings'].update(tim=score(4.5, 3, 3)), contains='whole number from 0 to 5')

    def test_boolean_score_fails(self):
        self.check(lambda d: self.stops(d)[0]['ratings'].update(tim=score(True, 3, 3)), contains='whole number from 0 to 5')

    def test_missing_score_key_fails(self):
        self.check(lambda d: self.stops(d)[0]['ratings'].update(tim={'beer': 3, 'service': 3}), contains='need exactly beer, service and gl')

    # ---- references
    def test_unknown_person_fails(self):
        self.check(lambda d: self.stops(d)[0]['ratings'].update(nobody=score(3, 3, 3)), contains='unknown person "nobody"')

    def test_unknown_brewery_fails(self):
        self.check(lambda d: self.stops(d).append({'brewery': 'nowhere', 'ratings': {}}), contains='unknown brewery "nowhere"')

    def test_brewery_twice_in_a_season_fails(self):
        self.check(lambda d: self.stops(d, 1).append({'brewery': 'alpha', 'ratings': {}}), contains='already in')

    # ---- dates and times
    def test_stage_dates_out_of_order_fail(self):
        def m(d):
            d['seasons']['2026']['stages'][1]['date'] = '2026-04-01'
        self.check(m, contains='oldest first')

    def test_impossible_date_fails(self):
        def m(d):
            d['seasons']['2026']['stages'][0]['date'] = '2026-02-30'
        self.check(m, contains='must be a real date')

    def test_bad_time_fails(self):
        self.check(lambda d: self.stops(d)[0].update(start='25:00'), contains='must be a time like 16:00')

    def test_end_before_start_fails(self):
        self.check(lambda d: self.stops(d)[0].update(start='15:00', end='14:00'), contains='must be after')

    def test_end_without_start_fails(self):
        def m(d):
            s = self.stops(d)[1]
            s['end'] = '16:00'
        self.check(m, contains='needs a "start"')

    def test_negative_travel_fails(self):
        self.check(lambda d: self.stops(d)[0].update(travel=-5), contains='"travel" must be whole minutes')

    # ---- breweries
    def test_brewery_status_must_be_open_or_closed(self):
        self.check(lambda d: d['breweries']['breweries']['alpha'].update(status='maybe'), contains='status must be')

    def test_brews_on_site_must_be_boolean(self):
        self.check(lambda d: d['breweries']['breweries']['alpha'].update(brewsOnSite='no'), contains='brewsOnSite must be true or false')

    def test_empty_district_fails(self):
        self.check(lambda d: d['breweries']['breweries']['alpha'].update(district='  '), contains='district must be non-empty')

    def test_unknown_brewery_field_fails(self):
        self.check(lambda d: d['breweries']['breweries']['alpha'].update(colour='red'), contains='unknown fields')

    def test_brewery_id_must_be_lowercase_letters(self):
        def m(d):
            d['breweries']['breweries']['Bad_Id'] = d['breweries']['breweries'].pop('gamma')
        self.check(m, contains='lowercase letters only')

    def test_two_breweries_with_the_same_name_fail(self):
        self.check(lambda d: d['breweries']['breweries']['beta'].update(name='alpha'), contains='have the same name')

    # ---- manifest and files
    def test_weights_must_add_up_to_one(self):
        self.check(lambda d: d['manifest']['weights'].update(beer=0.9), contains='add up to 1')

    def test_seasons_must_be_listed_oldest_first(self):
        def m(d):
            d['manifest']['seasons'] = ['2027', '2026']
            d['seasons']['2027'] = dict(d['seasons']['2026'], id='2027', label='2027')
        self.check(m, contains='oldest first')

    def test_season_file_id_must_match(self):
        self.check(lambda d: d['seasons']['2026'].update(id='2030'), contains='"id" must be "2026"')

    def test_missing_season_file_fails(self):
        def m(d):
            d['manifest']['seasons'] = ['2026', '2027']
        self.check(m, contains='file not found')

    def test_duplicate_json_key_fails(self):
        data = self.data()
        write(os.path.join(data, 'people.json'), '{"version": 1, "people": {"ines": {"name": "A"}, "ines": {"name": "B"}}}')
        code, out = run(VALIDATE, data, '--index', os.path.join(self.tmp, 'none.html'))
        self.assertEqual(code, 1)
        self.assertIn('duplicate key', out)

    def test_season_file_not_in_manifest_is_only_a_warning(self):
        def m(d):
            d['seasons']['2020'] = dict(d['seasons']['2026'], id='2020', label='2019/2020')
        out = self.check(m, ok=True)
        self.assertIn('not listed in manifest.json', out)

    def test_person_without_ratings_is_only_a_warning(self):
        out = self.check(lambda d: d['people']['people'].update(zed={'name': 'Zed'}), ok=True)
        self.assertIn('person "zed" has no ratings', out)

    # ---- the live page must not carry test data
    def page(self, block):
        path = os.path.join(self.tmp, 'index.html')
        write(path, '<html><script type="application/json" id="tdbb-data">%s</script></html>' % block)
        return path

    def test_empty_data_block_passes(self):
        code, out = run(VALIDATE, self.data(), '--index', self.page(''))
        self.assertEqual(code, 0, out)

    def test_embedded_test_data_fails(self):
        code, out = run(VALIDATE, self.data(), '--index', self.page('{"manifest": {}}'))
        self.assertEqual(code, 1)
        self.assertIn('test data is embedded', out)

    def test_missing_data_block_fails(self):
        path = os.path.join(self.tmp, 'index.html')
        write(path, '<html></html>')
        code, out = run(VALIDATE, self.data(), '--index', path)
        self.assertEqual(code, 1)
        self.assertIn('data block', out)


if __name__ == '__main__':
    unittest.main()
