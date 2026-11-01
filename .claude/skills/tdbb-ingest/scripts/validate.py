#!/usr/bin/env python3
"""Validate the TDBB data files. Exit code 0 = OK, 1 = problems found.

Usage:
  python3 validate.py [DATA_DIR] [--index PATH_TO_INDEX_HTML]

DATA_DIR defaults to ./data. If --index is given (or ./index.html exists next to
DATA_DIR) the script also checks that no test data is embedded in the live page.
Only the Python standard library is used.
"""
import json, os, re, sys
from datetime import date

ID_RE = re.compile(r'^[a-z]+$')
TIME_RE = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')
SEASON_ID_RE = re.compile(r'^\d{4}$')
LABEL_RE = re.compile(r'^\d{4}(/\d{4})?$')
SCORE_KEYS = ('beer', 'service', 'gl')

errors, warnings, infos = [], [], []


def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)


def no_duplicates(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError('duplicate key "%s"' % k)
        seen[k] = v
    return seen


def load(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f, object_pairs_hook=no_duplicates)
    except FileNotFoundError:
        err('%s: file not found' % path)
    except ValueError as e:
        err('%s: not valid JSON (%s)' % (path, e))
    return None


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def check_version(obj, name):
    if obj.get('version') != 1:
        err('%s: "version" must be 1' % name)


def check_manifest(m, path):
    check_version(m, path)
    w = m.get('weights')
    if not isinstance(w, dict) or set(w) != set(SCORE_KEYS):
        err('%s: "weights" needs exactly beer, service and gl' % path)
    else:
        if any(isinstance(w[k], bool) or not isinstance(w[k], (int, float)) or w[k] < 0 for k in w):
            err('%s: weights must be numbers >= 0' % path)
        elif abs(sum(w.values()) - 1) > 1e-9:
            err('%s: weights must add up to 1 (now %s)' % (path, sum(w.values())))
    s = m.get('seasons')
    if not isinstance(s, list) or not s:
        err('%s: "seasons" must be a non-empty list' % path)
        return []
    if len(set(s)) != len(s):
        err('%s: duplicate season ids' % path)
    for sid in s:
        if not isinstance(sid, str) or not SEASON_ID_RE.match(sid):
            err('%s: season id "%s" must be a four digit year, like "2026"' % (path, sid))
    if s != sorted(s):
        err('%s: seasons must be listed oldest first' % path)
    return [x for x in s if isinstance(x, str)]


def check_people(p, path):
    check_version(p, path)
    people = p.get('people')
    if not isinstance(people, dict) or not people:
        err('%s: "people" must be an object with at least one person' % path)
        return {}
    names = {}
    for pid, v in people.items():
        if not ID_RE.match(pid):
            err('%s: person id "%s" must be lowercase letters only, one word' % (path, pid))
        if not isinstance(v, dict) or not isinstance(v.get('name'), str) or not v['name'].strip():
            err('%s: person "%s" needs a "name"' % (path, pid))
            continue
        extra = set(v) - {'name'}
        if extra:
            err('%s: person "%s" has unknown fields %s (people have no aliases)' % (path, pid, sorted(extra)))
        low = v['name'].strip().lower()
        if low in names:
            err('%s: "%s" and "%s" have the same name' % (path, names[low], pid))
        names[low] = pid
    return people


def check_breweries(b, path):
    check_version(b, path)
    br = b.get('breweries')
    if not isinstance(br, dict) or not br:
        err('%s: "breweries" must be an object with at least one brewery' % path)
        return {}
    names = {}
    for bid, v in br.items():
        if not ID_RE.match(bid):
            err('%s: brewery id "%s" must be lowercase letters only, one word' % (path, bid))
        if not isinstance(v, dict):
            err('%s: brewery "%s" must be an object' % (path, bid))
            continue
        for k in ('name', 'address', 'highlight'):
            if not isinstance(v.get(k), str) or not v[k].strip():
                err('%s: brewery "%s" needs a non-empty "%s"' % (path, bid, k))
        if v.get('status') not in ('open', 'closed'):
            err('%s: brewery "%s" status must be "open" or "closed"' % (path, bid))
        if 'brewsOnSite' in v and not isinstance(v['brewsOnSite'], bool):
            err('%s: brewery "%s" brewsOnSite must be true or false' % (path, bid))
        if 'district' in v and (not isinstance(v['district'], str) or not v['district'].strip()):
            err('%s: brewery "%s" district must be non-empty text' % (path, bid))
        extra = set(v) - {'name', 'address', 'district', 'highlight', 'status', 'brewsOnSite'}
        if extra:
            err('%s: brewery "%s" has unknown fields %s' % (path, bid, sorted(extra)))
        if isinstance(v.get('name'), str):
            low = v['name'].strip().lower()
            if low in names:
                err('%s: "%s" and "%s" have the same name' % (path, names[low], bid))
            names[low] = bid
    return br


def parse_date(s):
    try:
        y, m, d = s.split('-')
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def check_season(sid, season, path, people, breweries, used_people, used_breweries):
    check_version(season, path)
    if season.get('id') != sid:
        err('%s: "id" must be "%s" (the file name)' % (path, sid))
    label = season.get('label')
    if not isinstance(label, str) or not LABEL_RE.match(label):
        err('%s: "label" must look like "2025/2026" or "2027"' % path)
    stages = season.get('stages')
    if not isinstance(stages, list) or not stages:
        err('%s: "stages" must be a non-empty list' % path)
        return 0
    seen_breweries = {}
    prev = None
    n_ratings = 0
    for si, st in enumerate(stages, 1):
        where = '%s stage %d' % (path, si)
        d = parse_date(st.get('date')) if isinstance(st, dict) and isinstance(st.get('date'), str) else None
        if d is None:
            err('%s: "date" must be a real date like 2026-10-31' % where)
        else:
            if prev and d <= prev:
                err('%s: stage dates must be in order, oldest first' % where)
            prev = d
        stops = st.get('stops') if isinstance(st, dict) else None
        if not isinstance(stops, list):
            err('%s: "stops" must be a list (empty for a stage that is planned but has no agenda yet)' % where)
            continue
        for pi, sp in enumerate(stops, 1):
            w = '%s stop %d' % (where, pi)
            if not isinstance(sp, dict):
                err('%s: must be an object' % w)
                continue
            bid = sp.get('brewery')
            if bid not in breweries:
                err('%s: unknown brewery "%s" (add it to breweries.json first)' % (w, bid))
            else:
                used_breweries.add(bid)
                if bid in seen_breweries:
                    err('%s: brewery "%s" is already in %s' % (w, bid, seen_breweries[bid]))
                seen_breweries[bid] = w
            extra = set(sp) - {'brewery', 'start', 'end', 'travel', 'note', 'ratings'}
            if extra:
                err('%s: unknown fields %s' % (w, sorted(extra)))
            for k in ('start', 'end'):
                if k in sp and (not isinstance(sp[k], str) or not TIME_RE.match(sp[k])):
                    err('%s: "%s" must be a time like 16:00' % (w, k))
            if 'end' in sp and 'start' not in sp:
                err('%s: "end" needs a "start"' % w)
            if isinstance(sp.get('start'), str) and isinstance(sp.get('end'), str) and \
               TIME_RE.match(sp['start']) and TIME_RE.match(sp['end']) and sp['end'] <= sp['start']:
                err('%s: "end" must be after "start"' % w)
            if 'travel' in sp and (not is_int(sp['travel']) or sp['travel'] < 0):
                err('%s: "travel" must be whole minutes, 0 or more' % w)
            if 'note' in sp and not isinstance(sp['note'], str):
                err('%s: "note" must be text' % w)
            ratings = sp.get('ratings')
            if not isinstance(ratings, dict):
                err('%s: "ratings" must be an object (use {} for none yet)' % w)
                continue
            if not ratings:
                infos.append('%s (%s): no ratings yet' % (w, bid))
            for pid, r in ratings.items():
                if pid not in people:
                    err('%s: unknown person "%s" (add them to people.json first)' % (w, pid))
                else:
                    used_people.add(pid)
                if not isinstance(r, dict) or set(r) != set(SCORE_KEYS):
                    err('%s: scores for "%s" need exactly beer, service and gl' % (w, pid))
                    continue
                for k in SCORE_KEYS:
                    if not is_int(r[k]) or not 0 <= r[k] <= 5:
                        err('%s: %s score for "%s" must be a whole number from 0 to 5 (got %r)' % (w, k, pid, r[k]))
                n_ratings += 1
    return n_ratings


def check_index(path):
    try:
        html = open(path, encoding='utf-8').read()
    except FileNotFoundError:
        return
    m = re.search(r'<script[^>]*id="tdbb-data"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        err('%s: the data block <script id="tdbb-data"> is missing' % path)
    elif m.group(1).strip():
        err('%s: test data is embedded in this page. The live index.html must keep the data block empty' % path)


def main(argv):
    data_dir, index = 'data', None
    args = argv[1:]
    while args:
        a = args.pop(0)
        if a == '--index' and args:
            index = args.pop(0)
        else:
            data_dir = a
    manifest = load(os.path.join(data_dir, 'manifest.json'))
    people_f = load(os.path.join(data_dir, 'people.json'))
    brew_f = load(os.path.join(data_dir, 'breweries.json'))
    seasons = []
    if manifest is not None:
        seasons = check_manifest(manifest, 'manifest.json')
    people = check_people(people_f, 'people.json') if people_f is not None else {}
    breweries = check_breweries(brew_f, 'breweries.json') if brew_f is not None else {}
    used_people, used_breweries, total = set(), set(), 0
    files = set()
    sdir = os.path.join(data_dir, 'seasons')
    for sid in seasons:
        files.add(sid + '.json')
        path = os.path.join(sdir, sid + '.json')
        s = load(path)
        if s is not None:
            total += check_season(sid, s, 'seasons/%s.json' % sid, people, breweries, used_people, used_breweries)
    if os.path.isdir(sdir):
        for f in sorted(os.listdir(sdir)):
            if f.endswith('.json') and f not in files:
                warn('seasons/%s is not listed in manifest.json, so the page ignores it' % f)
    for pid in people:
        if pid not in used_people:
            warn('person "%s" has no ratings in any season' % pid)
    for bid in breweries:
        if bid not in used_breweries:
            warn('brewery "%s" is not in any season' % bid)
    if index is None:
        guess = os.path.join(os.path.dirname(os.path.abspath(data_dir)), 'index.html')
        index = guess if os.path.exists(guess) else None
    if index:
        check_index(index)
    for m in warnings:
        print('warning:', m)
    for m in infos:
        print('note:', m)
    for m in errors:
        print('ERROR:', m)
    if errors:
        print('\nNOT OK: %d problem(s). Do not publish these files.' % len(errors))
        return 1
    print('OK: %d season(s), %d people, %d breweries, %d ratings.' % (len(seasons), len(people), len(breweries), total))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
