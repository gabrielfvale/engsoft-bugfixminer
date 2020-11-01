import pandas
from pydriller import Commit
from pydriller import RepositoryMining
from pydriller.domain.commit import ModificationType
from datetime import datetime
from .mining_utils import filter_top_frequent_words, is_Test
from .mining_utils import is_Valid_Key, has_Source_Extension, extract_Keys
from .jira_mining import load_Jira_BugFix_Dataset


# =========================Git mining related code========================= #


class GitBugInfo:
    def __init__(self, key):
        self.key = key
        self.hasMergeCommit = 0
        self.commitsMessages = []
        self.numberOfCommits = 0
        self.authors = []
        self.committers = []
        self.authorsFirstCommitDate = None
        self.authorsLastCommitDate = None
        self.committersFirstCommitDate = None
        self.committersLastCommitDate = None
        self.authorsDates = []
        self.committersDates = []
        self.nonSrcAddFiles = 0
        self.nonSrcDelFiles = 0
        self.nonSrcModFiles = 0
        self.nonSrcAddLines = 0
        self.nonSrcDelLines = 0
        self.srcAddFiles = 0
        self.srcDelFiles = 0
        self.srcModFiles = 0
        self.srcAddLines = 0
        self.srcDelLines = 0
        self.testAddFiles = 0
        self.testDelFiles = 0
        self.testModFiles = 0
        self.testAddLines = 0
        self.testDelLines = 0

    def to_list(self):
        commitMessageTopWords = filter_top_frequent_words('\n'.join(
                [message for
                 message in self.commitsMessages]))

        if(len(self.authorsDates) > 0):
            self.authorsDates.sort()
            self.authorsFirstCommitDate = self.authorsDates[0]
            self.authorsLastCommitDate = self.authorsDates[-1]

        if(len(self.committersDates) > 0):
            self.committersDates.sort()
            self.committersFirstCommitDate = self.committersDates[0]
            self.committersLastCommitDate = self.committersDates[-1]

        return [self.key,
                self.hasMergeCommit,
                commitMessageTopWords,
                self.numberOfCommits,
                len(set(self.authors)),
                len(set(self.committers)),
                self.authorsFirstCommitDate,
                self.authorsLastCommitDate,
                self.committersFirstCommitDate,
                self.committersLastCommitDate,
                self.nonSrcAddFiles,
                self.nonSrcDelFiles,
                self.nonSrcModFiles,
                self.nonSrcAddLines,
                self.nonSrcDelLines,
                self.srcAddFiles,
                self.srcDelFiles,
                self.srcModFiles,
                self.srcAddLines,
                self.srcDelLines,
                self.testAddFiles,
                self.testDelFiles,
                self.testModFiles,
                self.testAddLines,
                self.testDelLines]


def fill_git_bug_info(
            bugInfo: GitBugInfo,
            commit: Commit) -> None:
    if(commit.merge):
        bugInfo.hasMergeCommit = 1

    bugInfo.commitsMessages.append(commit.msg)
    bugInfo.authorsDates.append(commit.author_date.isoformat())
    bugInfo.authors.append(commit.author.name)
    bugInfo.committers.append(commit.committer.name)
    bugInfo.committersDates.append(commit.committer_date.isoformat())
    bugInfo.numberOfCommits += 1

    for modification in commit.modifications:

        if(modification.old_path is not None):
            path = modification.old_path
        else:
            path = modification.new_path

        if(has_Source_Extension(modification.filename)):
            if(is_Test(path)):
                if(modification.change_type == ModificationType.ADD):
                    bugInfo.testAddFiles += 1

                elif(modification.change_type == ModificationType.DELETE):
                    bugInfo.testDelFiles += 1

                else:
                    bugInfo.testModFiles += 1

                bugInfo.testAddLines += modification.added
                bugInfo.testDelLines += modification.removed

            else:
                if(modification.change_type == ModificationType.ADD):
                    bugInfo.srcAddFiles += 1

                elif(modification.change_type == ModificationType.DELETE):
                    bugInfo.srcDelFiles += 1

                else:
                    bugInfo.srcModFiles += 1

                bugInfo.srcAddLines += modification.added
                bugInfo.srcDelLines += modification.removed

        else:
            if(modification.change_type == ModificationType.ADD):
                bugInfo.nonSrcAddFiles += 1

            elif(modification.change_type == ModificationType.DELETE):
                bugInfo.nonSrcDelFiles += 1

            else:
                bugInfo.nonSrcModFiles += 1

            bugInfo.nonSrcAddLines += modification.added
            bugInfo.nonSrcDelLines += modification.removed


def fetch_BugFix_Info_From_Git(
            git_repositories: list,
            jira_issues_keys: list,
            since_date: datetime,
            to_date: datetime) -> list:
    issues = {}
    offset = 0
    interation = 1
    for issue_key in jira_issues_keys:
        issues[issue_key.upper().strip()] = GitBugInfo(
                issue_key.upper().strip())

    for commit in RepositoryMining(
                path_to_repo=git_repositories,
                since=since_date,
                to=to_date).traverse_commits():
        message = commit.msg.upper().strip()
        keys_in_message = extract_Keys(message)

        for issue_key in jira_issues_keys:
            if(issue_key in keys_in_message):
                fill_git_bug_info(issues[issue_key], commit)
                offset += 1

                if(offset == 500):
                    print("  [Step 2.3."
                          + str(interation)
                          + "] "
                          + str(offset)
                          + " bug-related commits fetched from Git...")
                    interation += 1
                    offset = 0

                if(len(keys_in_message) <= 1):
                    break

    if(offset > 0):
        print("  [Step 2.3."
              + str(interation)
              + "] "
              + str(offset)
              + " bug-related commits fetched from Git...")

    return [values for values in issues.values()]


def git_To_CSV(project: str, issues: list) -> None:

    header = ['Key',
              'HasMergeCommit',
              'CommitsMessagesTopWords',
              'NoCommits',
              'NoAuthors',
              'NoCommitters',
              'AuthorsFirstCommitDate',
              'AuthorsLastCommitDate',
              'CommittersFirstCommitDate',
              'CommittersLastCommitDate',
              'NonSrcAddFiles',
              'NonSrcDelFiles',
              'NonSrcModFiles',
              'NonSrcAddLines',
              'NonSrcDelLines',
              'SrcAddFiles',
              'SrcDelFiles',
              'SrcModFiles',
              'SrcAddLines',
              'SrcDelLines',
              'TestAddFiles',
              'TestDelFiles',
              'TestModFiles',
              'TestAddLines',
              'TestDelLines']

    dataset = pandas.DataFrame(columns=header)

    for issue in issues:
        dataset = dataset.append(
                pandas.Series(issue.to_list(), index=dataset.columns),
                ignore_index=True)

    with open("dataset/snapshot/"
              + project.lower()
              + "-git-bug-fix-dataset.csv", 'a') as file:
        dataset.to_csv(file, sep=';', encoding='utf-8', index=False)


def mine_git(
            git_repositories: list,
            project: str,
            since_date: datetime,
            to_date: datetime) -> None:

    mined_issues = []

    print("  [Step-2.1] Loading CSV file with bug-fix info from Jira...")
    jira_issues = load_Jira_BugFix_Dataset(project)

    print("  [Step-2.2] Selecting bug issues keys from Jira bug-fix info...")
    project_issues_keys = jira_issues['Key'].to_list()

    print("  [Step-2.3] Fetching bug-fix info from Git...")
    mined_issues = fetch_BugFix_Info_From_Git(
            git_repositories,
            project_issues_keys,
            since_date,
            to_date)

    print("  [Step-2.4] Saving bug-fix info into CSV file...")
    git_To_CSV(project, mined_issues)


def load_Git_BugFix_Dataset(project: str) -> pandas.DataFrame:
    return pandas.read_csv("dataset/snapshot/"
                           + project.lower()
                           + "-git-bug-fix-dataset.csv",
                           index_col=None, header=0,
                           delimiter=';',
                           parse_dates=['AuthorsFirstCommitDate',
                                        'AuthorsLastCommitDate',
                                        'CommittersFirstCommitDate',
                                        'CommittersLastCommitDate'])
