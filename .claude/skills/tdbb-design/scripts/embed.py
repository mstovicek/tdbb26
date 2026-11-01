#!/usr/bin/env python3
"""Build a TEST copy of the page with the data embedded in it.

Usage:
  python3 embed.py [--data data] [--template index.html] [--out index-test.html]

The embedded copy works when opened directly or in a preview that cannot fetch files.
It shows a "Test data" banner. It is NEVER written to index.html: the live page must keep
its data block empty so it always reads the real files in data/.
"""
import importlib.util, json, os, re, sys
from datetime import datetime

here = os.path.dirname(os.path.abspath(__file__))


def fail(msg):
    print('ERROR:', msg)
    sys.exit(1)


def main(argv):
    data, template, out = 'data', 'index.html', 'index-test.html'
    args = argv[1:]
    while args:
        a = args.pop(0)
        if a == '--data' and args: data = args.pop(0)
        elif a == '--template' and args: template = args.pop(0)
        elif a == '--out' and args: out = args.pop(0)
        else: fail('unknown argument %r' % a)
    if os.path.basename(out).lower() == 'index.html':
        fail('refusing to write index.html. Embedded test data must never replace the live page. '
             'Use a different name, such as index-test.html.')
    if os.path.abspath(out) == os.path.abspath(template):
        fail('the output must be a different file from the template')

    # run the validator if the ingest skill is next to this one
    val = os.path.join(here, '..', '..', 'tdbb-ingest', 'scripts', 'validate.py')
    if os.path.exists(val):
        spec = importlib.util.spec_from_file_location('tdbb_validate', val)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if mod.main(['validate.py', data, '--index', template]) != 0:
            fail('the data failed validation, nothing was built')
    else:
        print('warning: validate.py not found, skipping validation')

    def load(p):
        with open(os.path.join(data, p), encoding='utf-8') as f:
            return json.load(f)
    manifest = load('manifest.json')
    bundle = {
        'builtAt': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'manifest': manifest,
        'people': load('people.json'),
        'breweries': load('breweries.json'),
        'seasons': {sid: load('seasons/%s.json' % sid) for sid in manifest['seasons']},
    }
    payload = json.dumps(bundle, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

    with open(template, encoding='utf-8') as f:
        html = f.read()
    pat = re.compile(r'(<script[^>]*id="tdbb-data"[^>]*>)(.*?)(</script>)', re.S)
    if not pat.search(html):
        fail('the template has no <script id="tdbb-data"> block')
    html = pat.sub(lambda m: m.group(1) + payload + m.group(3), html, count=1)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Wrote %s (%d KB, built %s)' % (out, len(html) // 1024, bundle['builtAt']))


if __name__ == '__main__':
    main(sys.argv)
