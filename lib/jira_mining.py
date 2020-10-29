from jira.client import JIRA
from jira.exceptions import JIRAError
from datetime import datetime
import pandas
from .mining_utils import isTest, isValidKey, filter_top_frequent_words


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
    query = 'project=' + jira_project + \
        ' and issuetype=bug and status in (Resolved, Closed) and resolution in (Fixed) and created>=\"' + \
        since_date + '\" and resolutiondate<=\"' + to_date + '\"'
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
        dataset = dataset.append(pandas.Series(
            issue.to_list(), index=dataset.columns), ignore_index=True)

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
