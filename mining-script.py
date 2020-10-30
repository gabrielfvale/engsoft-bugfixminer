# -*- coding: utf-8 -*-
"""
@author: anonymous
"""

import os
import sys
import pandas
import re
# os.system("pip3 install -r requirements.txt --user --upgrade")
from jira.client import JIRA
from jira.exceptions import JIRAError
from pydriller import Commit
from pydriller import RepositoryMining
from datetime import datetime
from lib.jira_mining import mine_jira, loadJiraBugFixDataset
from lib.mining_utils import isTest, hasSrcExtension, extractKeys
from lib.mining_utils import filter_top_frequent_words, isValidKey
from lib.git_mining import loadGitBugFixDataset, mine_git


projects_path = r'projects.csv'


# =======================Bug-Fix dataset mining code======================= #


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
        print(">Done! Duration time "
              + str(duration_time.total_seconds()) + "s")
        print("===================================================" +
              "===========================================================")
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
                    log = log.append(
                        pandas.Series(event, index=log.columns),
                        ignore_index=True)

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
        print(">Done! Duration time "
              + str(duration_time.total_seconds()) + "s")
        print("===================================================" +
              "===========================================================")


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
                    log = log.append(
                        pandas.Series(event, index=log.columns),
                        ignore_index=True)

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
        print(">Done! Duration time "
              + str(duration_time.total_seconds()) + "s")
        print("===================================================" +
              "===========================================================")


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
                        log = log.append(
                            pandas.Series(change, index=log.columns),
                            ignore_index=True)

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
        print(">Done! Duration time "
              + str(duration_time.total_seconds()) + "s")
        print("===================================================" +
              "===========================================================")

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
