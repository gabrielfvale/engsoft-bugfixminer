import pandas
from datetime import datetime
from lib.git_mining import load_Git_BugFix_Dataset, mine_git
from lib.jira_mining import load_Jira_BugFix_Dataset, mine_jira

# =======================Bug-Fix dataset mining code======================= #


def load_BugFix_Dataset(project: str) -> pandas.DataFrame:
    return pandas.read_csv("./dataset/snapshot/"
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


def run_Third_Step(project_key: str, project_name: str) -> None:
    print("  [Step-3.0] Joining and cleaning bug-fix info of "
          + project_name
          + " from Jira and Git repos")

    print("  [Step-3.1] Loading CSV with Jira bug-fix info...")
    jira_issues = load_Jira_BugFix_Dataset(project_key)

    print("  [Step-3.2] Loading CSV with Git bug-fix info...")
    git_issues = load_Git_BugFix_Dataset(project_key)

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

    with open("./dataset/snapshot/"
              + project_key.lower()
              + "-full-bug-fix-dataset.csv", 'a') as file:
        clean_dataset.to_csv(file, sep=';', encoding='utf-8', index=False)


def run_Second_Step(
            git_repository: list,
            project: str,
            since_date: datetime,
            to_date: datetime) -> None:
    print("  [Step-2.0] Extracting bug-fix info of "
          + project
          + " from Git repository...")
    mine_git(git_repository, project, since_date, to_date)


def run_First_Step(
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


def mine_BugFix(projects_path: str, since_date: datetime, to_date: datetime) -> None:
    projects = pandas.read_csv(projects_path,
                               index_col=None,
                               header=0,
                               delimiter=';')
    for _, row in projects.iterrows():
        start_date = datetime.now()
        print(">Building a bug-fix dataset for the "
              + row['Name']
              + " project ["
              + start_date.strftime('%Y-%m-%d %H:%M:%S') + "]")

        print(">Mining data sice " + str(since_date) + " to " + str(to_date))

        run_First_Step(row['JiraRepository'],
                       row['JiraName'],
                       row['Owner'],
                       row['Manager'],
                       row['Category'],
                       since_date,
                       to_date)

        run_Second_Step(row['GitRepository'].split('#'),
                        row['JiraName'],
                        since_date,
                        to_date)

        run_Third_Step(row['JiraName'], row['Name'])
        duration_time = datetime.now() - start_date
        print(">Done! Duration time "
              + str(duration_time.total_seconds()) + "s")
        print("===================================================" +
              "===========================================================")
        print()

