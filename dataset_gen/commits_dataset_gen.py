from datetime import datetime
import pandas
from pydriller import RepositoryMining, Commit
from lib.mining_utils import has_Source_Extension, is_Test, filter_top_frequent_words, extract_Keys
from .bugfix_dataset_gen import load_BugFix_Dataset

# =======================Bug commits log mining code======================= #

def fetch_Bug_CommitLog(
            project: str,
            manager: str,
            category: str,
            bug_key: str,
            commit: Commit) -> list:

    """Fetches Bug Commit log from a JIRA project.

    From a JIRA repository and its data, fetches the Commit Log of the project.

    Args:
        jira: JIRA bindings for Python.
        project: The name of the project to fetch.
        manager: The repository manager.
        category: The category the repository fits in.
        bug_key: The key of the bug to fetch commits of.
        commit: A commit related to the bug.

    Returns:
        A list of commits log.
    """

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

        if(has_Source_Extension(modification.filename)):
            isSrc = 1

            if(is_Test(file_path)):
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


def mine_Bugs_CommitsLog(projects_path: str, since_date: datetime, to_date: datetime) -> None:

    """Mines the bug commits log CSV file.

    Takes the input CSV and runs a few steps of processing to mine commits log
    data of bugfix repositories.

    Args:
        projects_path: The path of the project CSV.
    """

    last_repo = []

    projects = pandas.read_csv(projects_path,
                               index_col=None,
                               header=0,
                               delimiter=';')

    for _, row in projects.iterrows():
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
        dataset = load_BugFix_Dataset(row['JiraName'])

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
            keys_in_message = extract_Keys(message)

            for bug_key in bug_keys_list:
                if(bug_key in keys_in_message):
                    tracked_commits.append(commit.hash)
                    commit_changes = fetch_Bug_CommitLog(row['JiraName'],
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

        with open("./dataset/commit-log/"
                  + row['JiraName'].lower()
                  + "-bug-fix-commit-log-dataset.csv", 'a') as file:
            log.to_csv(file, sep=';', encoding='utf-8', index=False)

        duration_time = datetime.now() - start_date
        print(">Done! Duration time "
              + str(duration_time.total_seconds())
              + "s")
        print("===================================================" +
              "===========================================================")
