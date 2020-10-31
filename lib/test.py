import mining_utils as mu
import unittest


class MyTest(unittest.TestCase):
    def test(self):
        self.assertTrue(mu.hasSrcExtension("test.py"))

if __name__ == "__main__":
    unittest.main()
