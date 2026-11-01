"""Shared helpers for the script tests. Test data is built in temporary folders, never stored in the repo."""
import copy, json, os, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCRIPTS = os.path.join(ROOT, '.claude', 'skills')
VALIDATE = os.path.join(SCRIPTS, 'tdbb-ingest', 'scripts', 'validate.py')
SUMMARY = os.path.join(SCRIPTS, 'tdbb-ingest', 'scripts', 'summary.py')
EMBED = os.path.join(SCRIPTS, 'tdbb-design', 'scripts', 'embed.py')


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def run(script, *args, cwd=None):
    """Run a script the way a person would. Returns (exit code, stdout + stderr)."""
    p = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout + p.stderr


def brewery(name, **extra):
    b = {'name': name, 'address': name + ' Street 1, 10115 Berlin', 'highlight': 'A place.', 'status': 'open'}
    b.update(extra)
    return b


def score(beer, service, gl):
    return {'beer': beer, 'service': service, 'gl': gl}


def base_data():
    """A small valid data set: 3 people, 3 breweries, one season with two stages."""
    return {
        'manifest': {'version': 1, 'weights': {'beer': 0.5, 'service': 0.25, 'gl': 0.25}, 'seasons': ['2026']},
        'people': {'version': 1, 'people': {'ines': {'name': 'Ines'}, 'milan': {'name': 'Milan'}, 'tim': {'name': 'Tim'}}},
        'breweries': {'version': 1, 'breweries': {
            'alpha': brewery('Alpha'), 'beta': brewery('Beta'), 'gamma': brewery('Gamma')}},
        'seasons': {'2026': {'version': 1, 'id': '2026', 'label': '2025/2026', 'stages': [
            {'date': '2026-05-01', 'stops': [
                {'brewery': 'alpha', 'start': '14:00', 'end': '15:00', 'travel': 10,
                 'ratings': {'ines': score(4, 3, 3), 'milan': score(5, 4, 4)}},
                {'brewery': 'beta', 'ratings': {'tim': score(3, 3, 3)}}]},
            {'date': '2026-06-01', 'stops': [{'brewery': 'gamma', 'ratings': {}}]}]}},
    }


def write_data(root, d):
    """Write a data set (as returned by base_data) into root/data. Returns the data folder."""
    data = os.path.join(root, 'data')
    os.makedirs(os.path.join(data, 'seasons'), exist_ok=True)
    for name in ('manifest', 'people', 'breweries'):
        with open(os.path.join(data, name + '.json'), 'w', encoding='utf-8') as f:
            json.dump(d[name], f, ensure_ascii=False, indent=1)
    for sid, season in d['seasons'].items():
        with open(os.path.join(data, 'seasons', sid + '.json'), 'w', encoding='utf-8') as f:
            json.dump(season, f, ensure_ascii=False, indent=1)
    return data


class TempCase(unittest.TestCase):
    """A test with a fresh temporary folder in self.tmp."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='tdbb-test-')
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def data(self, mutate=None):
        d = copy.deepcopy(base_data())
        if mutate:
            mutate(d)
        return write_data(self.tmp, d)
