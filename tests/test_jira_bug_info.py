import lib.jira_mining as jm
import unittest
from unittest.mock import MagicMock


class TestJiraBugInfo(unittest.TestCase):

    def test_to_list(self):
        bug_info = jm.JiraBugInfo(
            'issue_project',
            'owner',
            'manager',
            'category',
            0, 0,
            0,
            'status'
        )
        bug_info_list = bug_info.to_list()

        bug_info_expected = ['issue_project', 'owner', 'manager', 'category', 0, 0, 'status', None, None, None,
                             None, None, None, None, None, None, None, None, 0, None, None, 0, 0, None, None, 0, None, None, None, None]

        for i in range(len(bug_info_expected)):
            self.assertEqual(bug_info_list[i], bug_info_expected[i])

    def test_fill_jira_bug_info(self):
        issue = MagicMock()
        jira = MagicMock()

        issue.mock_add_spec(['id', 'key', 'fields'])
        issue.id = 0
        issue.key = 0

        issue.fields = MagicMock()
        issue.fields.mock_add_spec(['priority', 'status'])
        
        issue.fields.priority = 0
        issue.fields.status = 0


        bug_info = jm.fill_jira_bug_info(
            issue,
            jira,
            'mock',
            'owner',
            'manager',
            'category'
        )

        bug_info_list = bug_info.to_list()
        bug_info_expected = ['mock', 'owner', 'manager', 'category', 0, 0, 0, None, None, None, None,
                            None, None, None, None, None, None, None, 0, None, None, 0, 0, None, None, 0, None, None, None, None]

        for i in range(len(bug_info_expected)):
            self.assertEqual(bug_info_list[i], bug_info_expected[i])

if __name__ == "__main__":
    unittest.main()
