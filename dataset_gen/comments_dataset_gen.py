import pandas
from jira.client import JIRA
from jira.exceptions import JIRAError
from datetime import datetime
from .bugfix_dataset_gen import load_BugFix_Dataset
from lib.mining_utils import filter_top_frequent_words, is_Valid_Key

# =======================Bug comments log mining code======================= #


def fetch_Bug_CommentsLog(
            jira: JIRA,
            project: str,
            manager: str,
            category: str,
            issue_key: str) -> list:

    """Fetches Bug Comments log from a JIRA project.

    From a JIRA repository and its data, fetches the Comments Log of the project.

    Args:
        jira: JIRA bindings for Python.
        project: The name of the project to fetch.
        manager: The repository manager.
        category: The category the repository fits in.
        issue_key: The key of the issue to fetch comments of.

    Returns:
        A list of comments log.
    """

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


def mine_Bugs_CommentsLog(projects_path: str) -> None:

    """Mines the bug comments log CSV file.

    Takes the input CSV and runs a few steps of processing to mine comments log
    data of bugfix repositories.

    Args:
        projects_path: The path of the project CSV.
    """

    last_repo = None

    projects = pandas.read_csv(projects_path,
                               index_col=None,
                               header=0,
                               delimiter=';')

    for _, row in projects.iterrows():
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
        dataset = load_BugFix_Dataset(row['JiraName'])

        issues_keys = dataset['Key'].to_list()
        print("  [Step-2.0] Mining comments log of "
              + str(len(issues_keys))
              + " bug issues...")

        if(last_repo is None or last_repo != row['JiraRepository']):
            last_repo = row['JiraRepository']
            jira_options = {'server': last_repo}
            jira = JIRA(options=jira_options)

        for issue_key in issues_keys:
            if(issue_key is not None and is_Valid_Key(issue_key)):
                offset += 1
                issue_timeline = fetch_Bug_CommentsLog(jira,
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
        with open("./dataset/comment-log/"
                  + row['JiraName'].lower()
                  + "-bug-fix-comment-log-dataset.csv", 'a') as file:
            log.to_csv(file, sep=';', encoding='utf-8', index=False)

        duration_time = datetime.now() - start_date
        print(">Done! Duration time "
              + str(duration_time.total_seconds()) + "s")
        print("===================================================" +
              "===========================================================")
