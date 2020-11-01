import lib.git_mining as gm 
import unittest
from unittest.mock import MagicMock

class GitBugInfo(unittest.TestCase):

    def test_to_list(self):

        bug_info = gm.GitBugInfo('key')
        bug_info_list = bug_info.to_list()

        bug_info_expected = ['key', 0, '', 0, 0, 0, None, None, None,
                            None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        self.assertEqual(bug_info_list, bug_info_expected)


if __name__ == "__main__":
    unittest.main()
