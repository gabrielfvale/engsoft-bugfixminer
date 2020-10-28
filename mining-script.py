# -*- coding: utf-8 -*-
"""
@author: anonymous
"""

import os
import sys
os.system("pip3 install -r requirements.txt --user --upgrade")

from jira.client import JIRA
from jira.exceptions import JIRAError
from pydriller import Commit
from pydriller import RepositoryMining
from pydriller.domain.commit import ModificationType
from datetime import datetime
import pandas
import re
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk import FreqDist
from nltk.tokenize import RegexpTokenizer

TOP_MOST_FREQUENT_WORDS = 1000

projects_path = r'projects.csv'


# ========================Jira mining related code======================== #

class JiraBugInfo:
    def __init__(self,
                 issue_project,
                 project_owner,
                 project_manager,
                 project_category,
                 issue_id, issue_key,
                 issue_priority,
                 issue_status):
        self.project = issue_project
        self.owner = project_owner
        self.manager = project_manager
        self.category = project_category
        self.id = issue_id
        self.key = issue_key
        self.priority = issue_priority
        self.status = issue_status
        self.reporter = None
        self.assignee = None
        self.components = None
        self.summaryTopWords = None
        self.descriptionTopWords = None
        self.commentsTopWords = None
        self.creationDate = None
        self.resolutionDate = None
        self.lastUpdateDate = None
        self.affectsVersions = None
        self.fixVersions = None
        self.numberOfComments = 0
        self.firstCommentDate = None
        self.lastCommentDate = None
        self.numberOfWatchers = 0
        self.numberOfAttachments = 0
        self.firstAttachmentDate = None
        self.lastAttachmentDate = None
        self.numberOfAttachedPatches = 0
        self.firstAttachedPatchDate = None
        self.lastAttachedPatchDate = None
        self.inwardIssueLinks = None
        self.outwardIssueLinks = None

    def to_list(self):
        self.summaryTopWords = filter_top_frequent_words(
                self.summaryTopWords)
        self.descriptionTopWords = filter_top_frequent_words(
                self.descriptionTopWords)
        self.commentsTopWords = filter_top_frequent_words(
                self.commentsTopWords)

        return [self.project,
                self.owner,
                self.manager,
                self.category,
                self.key,
                self.priority,
                self.status,
                self.reporter,
                self.assignee,
                self.components,
                self.summaryTopWords,
                self.descriptionTopWords,
                self.commentsTopWords,
                self.creationDate,
                self.resolutionDate,
                self.lastUpdateDate,
                self.affectsVersions,
                self.fixVersions,
                self.numberOfComments,
                self.firstCommentDate,
                self.lastCommentDate,
                self.numberOfWatchers,
                self.numberOfAttachments,
                self.firstAttachmentDate,
                self.lastAttachmentDate,
                self.numberOfAttachedPatches,
                self.firstAttachedPatchDate,
                self.lastAttachedPatchDate,
                self.inwardIssueLinks,
                self.outwardIssueLinks]


def fill_jira_bug_info(
            issue,
            jira: JIRA,
            jira_project: str,
            project_owner: str,
            project_manager: str,
            project_category: str) -> JiraBugInfo:

    bugInfo = JiraBugInfo(
            jira_project,
            project_owner,
            project_manager,
            project_category,
            issue.id, issue.key,
            issue.fields.priority,
            issue.fields.status)

    if(hasattr(issue.fields, "reporter")):
        if(issue.fields.reporter is not None):
            bugInfo.reporter = issue.fields.reporter.name

    if(hasattr(issue.fields, "assignee")):
        if(issue.fields.assignee is not None):
            bugInfo.assignee = issue.fields.assignee.name

    if(hasattr(issue.fields, "components")):
        if(issue.fields.components):
            bugInfo.components = ' '.join([
                    component.name for
                    component in issue.fields.components])

    if(hasattr(issue.fields, "issuelinks")):
        if(issue.fields.issuelinks):
            inwardIssueLinks = []
            outwardIssueLinks = []
            for link in issue.fields.issuelinks:
                if hasattr(link, "outwardIssue"):
                    outwardIssue = link.outwardIssue
                    outwardIssueLinks.append(
                            str(link.type.name)
                            + ":"
                            + str(outwardIssue.key))

                if hasattr(link, "inwardIssue"):
                    inwardIssue = link.inwardIssue
                    inwardIssueLinks.append(
                            str(link.type.name)
                            + ":"
                            + str(inwardIssue.key))

            bugInfo.inwardIssueLinks = '\n'.join(inwardIssueLinks)
            bugInfo.outwardIssueLinks = '\n'.join(outwardIssueLinks)

    if(hasattr(issue.fields, "summary")):
        if(issue.fields.summary is not None):
            bugInfo.summaryTopWords = str(issue.fields.summary)

    if(hasattr(issue.fields, "description")):
        if(issue.fields.description is not None):
            bugInfo.descriptionTopWords = str(issue.fields.description)

    if(hasattr(issue.fields, "created")):
        bugInfo.creationDate = issue.fields.created

    if(hasattr(issue.fields, "resolutiondate")):
        bugInfo.resolutionDate = issue.fields.resolutiondate

    if(hasattr(issue.fields, "updated")):
        bugInfo.lastUpdateDate = issue.fields.updated

    if(hasattr(issue.fields, "versions")):
        if(issue.fields.versions):
            bugInfo.affectsVersions = ' '.join(
                    [version.name for
                     version in reversed(issue.fields.versions)])

    if(hasattr(issue.fields, "fixVersions")):
        if(issue.fields.fixVersions):
            bugInfo.fixVersions = ' '.join(
                    [version.name for
                     version in reversed(issue.fields.fixVersions)])

    if(hasattr(issue.fields, "watches")):
        bugInfo.numberOfWatchers = jira.watchers(issue).watchCount

    if(hasattr(issue.fields, "attachment")):
        bugInfo.numberOfAttachments = len(issue.fields.attachment)

        attachment_dates = []
        patch_dates = []
        for attachment in issue.fields.attachment:
            attachment_dates.append(attachment.created)
            if 'patch' in attachment.filename:
                bugInfo.numberOfAttachedPatches += 1
                patch_dates.append(attachment.created)

        if(len(attachment_dates) > 0):
            attachment_dates.sort()
            bugInfo.firstAttachmentDate = attachment_dates[0]
            bugInfo.lastAttachmentDate = attachment_dates[-1]

        if(len(patch_dates) > 0):
            patch_dates.sort()
            bugInfo.firstAttachedPatchDate = patch_dates[0]
            bugInfo.lastAttachedPatchDate = patch_dates[-1]

    if(hasattr(issue.fields, "comment")):
        bugInfo.numberOfComments = len(issue.fields.comment.comments)

        comment_dates = []
        for comment in issue.fields.comment.comments:
            comment_dates.append(comment.created)

        if(len(comment_dates) > 0):
            comment_dates.sort()
            bugInfo.firstCommentDate = comment_dates[0]
            bugInfo.lastCommentDate = comment_dates[-1]

        if(issue.fields.comment.comments):
            bugInfo.commentsTopWords = '\n'.join(
                    [comment.body for
                     comment in issue.fields.comment.comments])

    return bugInfo


def fetch_bug_fix_info_from_jira(
            jira_repository: str,
            jira_project: str,
            project_owner: str,
            project_manager: str,
            project_category: str,
            offset: str,
            since_date: datetime,
            to_date: datetime) -> tuple:
    jira_options = {'server': jira_repository}
    jira = JIRA(options=jira_options)
    issue_fields = '''project,
                      id,
                      key,
                      priority,
                      status,
                      reporter,
                      assignee,
                      issuelinks,
                      summary,
                      description,
                      components,
                      comment,
                      created,
                      resolutiondate,
                      watchers,
                      attachment,
                      versions,
                      fixVersions'''
    query = 'project=' + jira_project + ' and issuetype=bug and status in (Resolved, Closed) and resolution in (Fixed) and created>=\"' + since_date + '\" and resolutiondate<=\"' + to_date + '\"'
    orderBy = ' order by id asc'

    fetched_issues = jira.search_issues(
            jql_str=(query + orderBy),
            fields=issue_fields,
            maxResults=offset)

    bugs = {}

    if(fetched_issues is None or len(fetched_issues) <= 0):
        print("  [Step-1.2.1] 0 bug issues fetched from Jira...")
        return bugs.values()

    length = len(fetched_issues)
    count = 0

    while (length > 0 and length <= offset):
        count += 1
        last_fetched_issue = fetched_issues[-1]
        print("  [Step-1.2."
              + str(count)
              + "] "
              + str(length)
              + " bug issues fetched from Jira...")

        for issue in fetched_issues:
            if(isValidKey(issue.key)):
                bugs[issue.key] = fill_jira_bug_info(
                        issue,
                        jira,
                        jira_project,
                        project_owner,
                        project_manager,
                        project_category)

        fetched_issues = jira.search_issues(jql_str=(query
                                            + ' and id>'
                                            + str(last_fetched_issue.id)
                                            + orderBy),
                                            fields=issue_fields,
                                            maxResults=offset)

        length = len(fetched_issues)

    return bugs.values()


def jiraToCSV(project: str, issues: tuple) -> None:

    header = ['Project',
              'Owner',
              'Manager',
              'Category',
              'Key',
              'Priority',
              'Status',
              'Reporter',
              'Assignee',
              'Components',
              'SummaryTopWords',
              'DescriptionTopWords',
              'CommentsTopWords',
              'CreationDate',
              'ResolutionDate',
              'LastUpdateDate',
              'AffectsVersions',
              'FixVersions',
              'NoComments',
              'FirstCommentDate',
              'LastCommentDate',
              'NoWatchers',
              'NoAttachments',
              'FirstAttachmentDate',
              'LastAttachmentDate',
              'NoAttachedPatches',
              'FirstAttachedPatchDate',
              'LastAttachedPatchDate',
              'InwardIssueLinks',
              'OutwardIssueLinks']

    dataset = pandas.DataFrame(columns=header)

    for issue in issues:
        dataset = dataset.append(pandas.Series(issue.to_list(), index=dataset.columns), ignore_index=True)

    with open("dataset/snapshot/"
              + project.lower()
              + "-jira-bug-fix-dataset.csv", 'a') as file:
        dataset.to_csv(file, sep=';', encoding='utf-8', index=False)


def mine_jira(
            jira_repository: str,
            project: str,
            owner: str,
            manager: str,
            category: str,
            since_date: datetime,
            to_date: datetime) -> None:
    print("  [Step-1.2] Fetching bug-fix info from Jira...")
    mined_issues = fetch_bug_fix_info_from_jira(
            jira_repository,
            project,
            owner,
            manager,
            category,
            500,
            since_date,
            to_date)

    print("  [Step-1.3] Saving bug-fix info into CSV file...")
    jiraToCSV(project, mined_issues)

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

        if(hasSrcExtension(modification.filename)):
            if(isTest(path)):
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


def fetchBugFixInfoFromGit(
            git_repositories: list,
            jira_issues_keys: list,
            since_date: datetime,
            to_date: datetime) -> list:
    issues = {}
    offset = 0
    interation = 1
    for issue_key in jira_issues_keys:
        issues[issue_key.upper().strip()] = GitBugInfo(issue_key.upper().strip())

    for commit in RepositoryMining(
                path_to_repo=git_repositories,
                since=since_date,
                to=to_date).traverse_commits():
        message = commit.msg.upper().strip()
        keys_in_message = extractKeys(message)

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
        print("  [Step 2.3." + str(interation) + "] " + str(offset) + " bug-related commits fetched from Git...")

    return [values for values in issues.values()]


def gitToCSV(project: str, issues: list) -> None:

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
        dataset = dataset.append(pandas.Series(issue.to_list(), index=dataset.columns), ignore_index=True)

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
    jira_issues = loadJiraBugFixDataset(project)

    print("  [Step-2.2] Selecting bug issues keys from Jira bug-fix info...")
    project_issues_keys = jira_issues['Key'].to_list()

    print("  [Step-2.3] Fetching bug-fix info from Git...")
    mined_issues = fetchBugFixInfoFromGit(
            git_repositories,
            project_issues_keys,
            since_date,
            to_date)

    print("  [Step-2.4] Saving bug-fix info into CSV file...")
    gitToCSV(project, mined_issues)


# ===========================Mining utility code=========================== #

def filter_top_frequent_words(text: str) -> str:
    if(text is not None):
        text = text.lower()

        # Removing code makro
        regex = r"\{code.*?\}.*?\{code\}"
        match = re.search(regex,
                          text,
                          re.MULTILINE | re.IGNORECASE | re.DOTALL)
        while(match is not None):
            code_block = match.group()
            text = text.replace(code_block, "")
            match = re.search(regex,
                              text,
                              re.MULTILINE | re.IGNORECASE | re.DOTALL)

        tokenizer = RegexpTokenizer(r'\w+')
        word_list = tokenizer.tokenize(text)

        # Clean digits
        non_digit_words = [word for word in word_list if not word.isdigit()]

        # Removing stop words
        non_stop_words = [word for word in
                          non_digit_words if
                          word not in
                          stopwords.words('english')]

        # Removing non english words
        english_words = [word for word in
                         non_stop_words if wordnet.synsets(word)]

        # Selecting top most frequent words
        fdist = FreqDist(english_words)
        top_words = fdist.most_common(TOP_MOST_FREQUENT_WORDS)
        text = ' '.join([str(top_word[0])
                        + ":" + str(top_word[1])
                        for top_word in top_words])

    return text


def hasSrcExtension(file_name: str) -> bool:
    src_extensions = (".clj",
                      ".scala",
                      ".java",
                      ".py",
                      ".sc",
                      ".js",
                      ".c",
                      ".hpp",
                      ".cpp"
                      ".rb",
                      ".go",
                      ".groovy",
                      ".pl",
                      ".pm",
                      ".t",
                      ".pod",
                      ".sh",
                      ".h",
                      ".php",
                      ".sql_in",
                      ".py_in")
    return file_name.endswith(src_extensions)


def isTest(file_path: str) -> bool:
    test_clues = ["/test/", "test/", "/test", "/tests/", "tests/", "/tests"]
    for clue in test_clues:
        if(clue in file_path):
            return True
    return False


def extractKeys(message: str) -> list:
    keys = []

    if(message is None):
        return keys

    for key in re.findall(r"[A-Z0-9]{2,}-\d+", message):
        keys.append(key)

    return keys


def isValidKey(message: str) -> None:
    if(message is None):
        return False

    if(re.match(r"[A-Z0-9]{2,}-\d+", message)):
        return True
    return False


# =======================Bug-Fix dataset mining code======================= #


def loadJiraBugFixDataset(project: str) -> pandas.DataFrame:
    return pandas.read_csv("dataset/snapshot/"
                           + project.lower()
                           + "-jira-bug-fix-dataset.csv",
                           index_col=None,
                           header=0,
                           delimiter=';',
                           parse_dates=['CreationDate',
                                        'ResolutionDate',
                                        'FirstCommentDate',
                                        'LastCommentDate',
                                        'FirstAttachmentDate',
                                        'LastAttachmentDate',
                                        'FirstAttachedPatchDate',
                                        'LastAttachedPatchDate'])


def loadGitBugFixDataset(project: str) -> pandas.DataFrame:
    return pandas.read_csv("dataset/snapshot/"
                           + project.lower()
                           + "-git-bug-fix-dataset.csv",
                           index_col=None, header=0,
                           delimiter=';',
                           parse_dates=['AuthorsFirstCommitDate',
                                        'AuthorsLastCommitDate',
                                        'CommittersFirstCommitDate',
                                        'CommittersLastCommitDate'])


def loadBugFixDataset(project: str) -> pandas.DataFrame:
    return pandas.read_csv("dataset/snapshot/"
                           + project.lower()
                           + "-full-bug-fix-dataset.csv",
                           index_col=None,
                           header=0,
                           delimiter=';',
                           parse_dates=['CreationDate',
                                        'ResolutionDate',
                                        'FirstCommentDate',
                                        'LastCommentDate',
                                        'FirstAttachmentDate',
                                        'LastAttachmentDate',
                                        'FirstAttachedPatchDate',
                                        'LastAttachedPatchDate',
                                        'AuthorsFirstCommitDate',
                                        'AuthorsLastCommitDate',
                                        'CommittersFirstCommitDate',
                                        'CommittersLastCommitDate'])


def runThirdStep(project_key: str, project_name: str) -> None:
    print("  [Step-3.0] Joining and cleaning bug-fix info of "
          + project_name
          + " from Jira and Git repos")

    print("  [Step-3.1] Loading CSV with Jira bug-fix info...")
    jira_issues = loadJiraBugFixDataset(project_key)

    print("  [Step-3.2] Loading CSV with Git bug-fix info...")
    git_issues = loadGitBugFixDataset(project_key)

    print("  [Step-3.3] Joining Jira and Git bug-fix infos...")
    raw_dataset = pandas.merge(jira_issues, git_issues, how='outer', on='Key')
    beforeCount = raw_dataset['Key'].count()

    print("  [Step-3.4] Cleaning joined dataset")
    clean_dataset = raw_dataset.query("Project=='" + project_key + "'")
    clean_dataset.drop_duplicates(keep='first', inplace=True)
    afterCount = clean_dataset['Key'].count()
    print("  [Step-3.5] " + str(beforeCount) + " bugs before cleaning...")
    print("  [Step-3.6] " + str(afterCount) + " bugs after cleaning...")
    print("  [Step-3.7] Saving the bug-fix dataset...")

    with open("dataset/snapshot/"
              + project_key.lower()
              + "-full-bug-fix-dataset.csv", 'a') as file:
        clean_dataset.to_csv(file, sep=';', encoding='utf-8', index=False)


def runSecondStep(
            git_repository: list,
            project: str,
            since_date: datetime,
            to_date: datetime) -> None:
    print("  [Step-2.0] Extracting bug-fix info of "
          + project
          + " from Git repository...")
    mine_git(git_repository, project, since_date, to_date)


def runFirstStep(
            jira_repository: str,
            project: str,
            owner: str,
            manager: str,
            category: str,
            since_date: datetime,
            to_date: datetime) -> None:
    print("  [Step-1.0] Extracting bug-fix info of "
          + project
          + " from Jira repo at: "
          + jira_repository)
    mine_jira(jira_repository,
              project,
              owner,
              manager,
              category,
              since_date.strftime("%Y/%m/%d"),
              to_date.strftime("%Y/%m/%d"))


def mineBugFix(since_date: datetime, to_date: datetime) -> None:
    projects = pandas.read_csv(projects_path,
                               index_col=None,
                               header=0,
                               delimiter=';')
    for index, row in projects.iterrows():
        start_date = datetime.now()
        print(">Building a bug-fix dataset for the "
              + row['Name']
              + " project ["
              + start_date.strftime('%Y-%m-%d %H:%M:%S') + "]")

        print(">Mining data sice " + str(since_date) + " to " + str(to_date))

        runFirstStep(row['JiraRepository'],
                     row['JiraName'],
                     row['Owner'],
                     row['Manager'],
                     row['Category'],
                     since_date,
                     to_date)

        runSecondStep(row['GitRepository'].split('#'),
                      row['JiraName'],
                      since_date,
                      to_date)

        runThirdStep(row['JiraName'], row['Name'])
        duration_time = datetime.now() - start_date
        print(">Done! Duration time " + str(duration_time.total_seconds()) + "s")
        print("==============================================================================================================")
        print()


# ====================Bug change log dataset mining code==================== #

def fetchBugChangeLog(
            jira: JIRA,
            project: str,
            manager: str,
            category: str,
            issue_key: str) -> list:
    events = []

    try:
        issue = jira.issue(issue_key, expand='changelog')
        changelog = issue.changelog
        fromString = None
        toString = None
        authorName = None
        for history in changelog.histories:
            for item in history.items:
                if(item.field in ['summary', 'description']):
                    fromString = filter_top_frequent_words(item.fromString)
                    toString = filter_top_frequent_words(item.toString)
                else:
                    fromString = item.fromString
                    toString = item.toString

                if(hasattr(history, "author")):
                    authorName = history.author.name
                else:
                    authorName = None

                events.append([project,
                               manager,
                               category,
                               issue_key,
                               authorName,
                               history.created,
                               item.field.lower().capitalize(),
                               fromString,
                               toString])

    except JIRAError as jiraError:
        print("Issue: ", issue_key)
        print("Status: ", str(jiraError.status_code))
        print("Message: ", str(jiraError.text))

    return events


def mineBugsChangeLog() -> None:

    last_repo = None

    projects = pandas.read_csv(projects_path,
                               index_col=None,
                               header=0,
                               delimiter=';')

    for index, row in projects.iterrows():
        log = pandas.DataFrame(columns=['Project',
                                        'Manager',
                                        'Category',
                                        'Key',
                                        'Author',
                                        'ChangeDate',
                                        'Field',
                                        'From',
                                        'To'])
        offset = 0
        count = 1
        start_date = datetime.now()
        print(">Building a bug change log for the "
              + row['Name']
              + " project ["
              + start_date.strftime('%Y-%m-%d %H:%M:%S') + "]")

        print("  [Step-1.0] Loading CSV with bug-fix info...")
        dataset = loadBugFixDataset(row['JiraName'])

        issues_keys = dataset['Key'].to_list()
        print("  [Step-2.0] Mining change log of "
              + str(len(issues_keys))
              + " bug issues...")

        if(last_repo is None or last_repo != row['JiraRepository']):
            last_repo = row['JiraRepository']
            jira_options = {'server': last_repo}
            jira = JIRA(options=jira_options)

        for issue_key in issues_keys:
            if(issue_key is not None and isValidKey(issue_key)):
                offset += 1
                issue_timeline = fetchBugChangeLog(jira,
                                                   row['JiraName'],
                                                   row['Manager'],
                                                   row['Category'],
                                                   issue_key)

                if(offset == 500):
                    print("  [Step-2.0." + str(count)
                          + "] Change log of "
                          + str(offset)
                          + " bug issues mined...")

                    count += 1
                    offset = 0

                for event in issue_timeline:
                    log = log.append(pandas.Series(event, index=log.columns), ignore_index=True)

        if(offset > 0):
            print("  [Step-2.0."
                  + str(count)
                  + "] Change log of "
                  + str(offset)
                  + " bug issues mined...")

        print("  [Step-3.0] Saving the bug-fix change log...")
        with open("dataset/changelog/"
                  + row['JiraName'].lower()
                  + "-bug-fix-changelog-dataset.csv", 'a') as file:
            log.to_csv(file, sep=';', encoding='utf-8', index=False)

        duration_time = datetime.now() - start_date
        print(">Done! Duration time " + str(duration_time.total_seconds()) + "s")
        print("==============================================================================================================")


# =======================Bug comments log mining code======================= #


def fetchBugCommentsLog(
            jira: JIRA,
            project: str,
            manager: str,
            category: str,
            issue_key: str) -> list:
    events = []

    try:
        issue = jira.issue(issue_key, fields="comment")

        if(hasattr(issue.fields, "comment")):
            for comment in issue.fields.comment.comments:
                events.append([project,
                               manager,
                               category,
                               issue_key,
                               comment.author.name,
                               comment.created,
                               filter_top_frequent_words(comment.body)])

    except JIRAError as jiraError:
        print("Issue: ", issue_key)
        print("Status: ", str(jiraError.status_code))
        print("Message: ", str(jiraError.text))

    return events


def mineBugsCommentsLog() -> None:

    last_repo = None

    projects = pandas.read_csv(projects_path,
                               index_col=None,
                               header=0,
                               delimiter=';')

    for index, row in projects.iterrows():
        log = pandas.DataFrame(columns=['Project',
                                        'Manager',
                                        'Category',
                                        'Key',
                                        'Author',
                                        'CreationDate',
                                        'Content'])
        offset = 0
        count = 1
        start_date = datetime.now()
        print(">Building a bug comments log for the "
              + row['Name']
              + " project ["
              + start_date.strftime('%Y-%m-%d %H:%M:%S') + "]")

        print("  [Step-1.0] Loading CSV with bug-fix info...")
        dataset = loadBugFixDataset(row['JiraName'])

        issues_keys = dataset['Key'].to_list()
        print("  [Step-2.0] Mining comments log of "
              + str(len(issues_keys))
              + " bug issues...")

        if(last_repo is None or last_repo != row['JiraRepository']):
            last_repo = row['JiraRepository']
            jira_options = {'server': last_repo}
            jira = JIRA(options=jira_options)

        for issue_key in issues_keys:
            if(issue_key is not None and isValidKey(issue_key)):
                offset += 1
                issue_timeline = fetchBugCommentsLog(jira,
                                                     row['JiraName'],
                                                     row['Manager'],
                                                     row['Category'],
                                                     issue_key)

                if(offset == 500):
                    print("  [Step-2.0."
                          + str(count)
                          + "] Comments log of "
                          + str(offset)
                          + " bug issues mined...")

                    count += 1
                    offset = 0

                for event in issue_timeline:
                    log = log.append(pandas.Series(event, index=log.columns), ignore_index=True)

        if(offset > 0):
            print("  [Step-2.0."
                  + str(count)
                  + "] Comments log of "
                  + str(offset)
                  + " bug issues mined...")

        print("  [Step-3.0] Saving the bug-fix comments log...")
        with open("dataset/comment-log/"
                  + row['JiraName'].lower()
                  + "-bug-fix-comment-log-dataset.csv", 'a') as file:
            log.to_csv(file, sep=';', encoding='utf-8', index=False)

        duration_time = datetime.now() - start_date
        print(">Done! Duration time " + str(duration_time.total_seconds()) + "s")
        print("==============================================================================================================")


# =======================Bug commits log mining code======================= #

def fetchBugCommitLog(
            project: str,
            manager: str,
            category: str,
            bug_key: str,
            commit: Commit) -> list:
    events = []

    isMerge = 0

    if(commit.merge):
        isMerge = 1

    for modification in commit.modifications:
        file_path = None

        if(modification.old_path is not None):
            file_path = modification.old_path
        else:
            file_path = modification.new_path

        isSrc = 0

        is_test = 0

        if(hasSrcExtension(modification.filename)):
            isSrc = 1

            if(isTest(file_path)):
                is_test = 1

        events.append([project,
                       manager,
                       category,
                       bug_key,
                       commit.hash,
                       isMerge,
                       commit.author.name,
                       commit.author_date.isoformat(),
                       commit.committer.name,
                       commit.committer_date.isoformat(),
                       filter_top_frequent_words(commit.msg),
                       modification.filename,
                       file_path,
                       modification.change_type.name,
                       isSrc,
                       is_test,
                       modification.added,
                       modification.removed,
                       len(modification.methods),
                       modification.nloc,
                       modification.complexity,
                       modification.token_count])

    return events


def mineBugsCommitsLog(since_date: datetime, to_date: datetime) -> None:
    last_repo = []

    projects = pandas.read_csv(projects_path,
                               index_col=None,
                               header=0,
                               delimiter=';')

    for index, row in projects.iterrows():
        log = pandas.DataFrame(columns=['Project',
                                        'Manager',
                                        'Category',
                                        'Key',
                                        'CommitHash',
                                        'IsMergeCommit',
                                        'Author',
                                        'AuthorDate',
                                        'Committer',
                                        'CommitterDate',
                                        'CommitMessageTopWords',
                                        'FileName',
                                        'FilePath',
                                        'ChangeType',
                                        'IsSrcFile',
                                        'IsTestFile',
                                        'AddLines',
                                        'DelLines',
                                        'NoMethods',
                                        'LoC',
                                        'CyC',
                                        'NoTokens'])
        tracked_commits = []
        interation = 1

        start_date = datetime.now()
        print(">Building a bug commits log for the "
              + row['Name']
              + " project ["
              + start_date.strftime('%Y-%m-%d %H:%M:%S') + "]")

        print("  [Step-1.0] Loading CSV with bug-fix info...")
        dataset = loadBugFixDataset(row['JiraName'])

        bug_keys_list = dataset['Key'].to_list()
        print("  [Step-2.0] Mining commits log of "
              + str(len(bug_keys_list))
              + " bug issues...")

        if(last_repo != row['GitRepository'].split('#')):
            last_repo = row['GitRepository'].split('#')

        for commit in RepositoryMining(path_to_repo=last_repo,
                                       since=since_date,
                                       to=to_date).traverse_commits():
            message = commit.msg.upper().strip()
            keys_in_message = extractKeys(message)

            for bug_key in bug_keys_list:
                if(bug_key in keys_in_message):
                    tracked_commits.append(commit.hash)
                    commit_changes = fetchBugCommitLog(row['JiraName'],
                                                       row['Manager'],
                                                       row['Category'],
                                                       bug_key,
                                                       commit)

                    for change in commit_changes:
                        log = log.append(pandas.Series(change, index=log.columns), ignore_index=True)

                    if(len(keys_in_message) <= 1):
                        break

            if(len(set(tracked_commits)) == 500):
                print("  [Step 2.0."
                      + str(interation)
                      + "] Commits log of "
                      + str(len(set(tracked_commits)))
                      + " commits performed...")

                interation += 1
                tracked_commits = []

        if(len(set(tracked_commits)) > 0):
            print("  [Step 2.0."
                  + str(interation)
                  + "] Commits log of "
                  + str(len(set(tracked_commits)))
                  + " commits performed...")

        print("  [Step-3.0] Saving the bug-fix commits log...")

        with open("dataset/commit-log/"
                  + row['JiraName'].lower()
                  + "-bug-fix-commit-log-dataset.csv", 'a') as file:
            log.to_csv(file, sep=';', encoding='utf-8', index=False)

        duration_time = datetime.now() - start_date
        print(">Done! Duration time " + str(duration_time.total_seconds()) + "s")
        print("==============================================================================================================")

# ==============================Run study code============================== #

since_date = datetime.strptime(str(sys.argv[1]), '%Y-%m-%d')
to_date = datetime.strptime(str(sys.argv[2]), '%Y-%m-%d')
projects_path = str(sys.argv[3])

print("============================================BUG-FIX DATASET GEN=======================================================")
mineBugFix(since_date, to_date)
print()
print()
print("============================================BUG CHANGE LOG DATASET GEN================================================")
mineBugsChangeLog()
print()
print()
print("============================================BUG COMMENTS DATASET GEN=================================================")
mineBugsCommentsLog()
print()
print()
print("============================================BUG COMMITS LOG DATASET GEN==============================================")
mineBugsCommitsLog(since_date, to_date)
