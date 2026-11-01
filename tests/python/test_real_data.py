import os, unittest
from helpers import ROOT, VALIDATE, read, run


class RealDataTests(unittest.TestCase):
    def test_the_real_data_is_valid(self):
        code, out = run(VALIDATE, os.path.join(ROOT, 'data'), '--index', os.path.join(ROOT, 'index.html'))
        self.assertEqual(code, 0, out)

    def test_live_page_has_an_empty_data_block(self):
        html = read(os.path.join(ROOT, 'index.html'))
        self.assertIn('<script type="application/json" id="tdbb-data"></script>', html)


if __name__ == '__main__':
    unittest.main()
