# -*- coding: utf-8 -*-
"""
@author: anonymous
"""

import argparse
import os
import sys
from datetime import datetime

from dataset_gen.bugfix_dataset_gen import mine_BugFix
from dataset_gen.changelog_dataset_gen import mine_Bugs_ChangeLog
from dataset_gen.comments_dataset_gen import mine_Bugs_CommentsLog
from dataset_gen.commits_dataset_gen import mine_Bugs_CommitsLog


# ==============================Run study code============================== #

def main():
    projects_path = os.path.join("projects.csv")

    main_parser = argparse.ArgumentParser(
        description="Bug fix miner using JIRA and GIT")

    period_parser = argparse.ArgumentParser(add_help=False)
    period_parser.add_argument(
        "period", nargs=2, help="The period to generate the dataset")

    path_parser = argparse.ArgumentParser(add_help=False)
    path_parser.add_argument(
        "-p", "--path", help="The projects PATH", default="projects.csv")

    # Create subparsers
    subparsers = main_parser.add_subparsers(title="actions", dest="action")

    # BUG-FIX DATASET GEN
    subparsers.add_parser("bugfix", parents=[period_parser, path_parser],
                          description="BUG-FIX DATASET GEN",
                          help="Generate bugfix dataset")
    # BUG CHANGE LOG DATASET GEN
    subparsers.add_parser("changelog", parents=[path_parser],
                          description="BUG CHANGE LOG DATASET GEN",
                          help="Generate changelog dataset")
    # BUG COMMENTS DATASET GEN
    subparsers.add_parser("comments", parents=[path_parser],
                          description="BUG-FIX DATASET GEN",
                          help="Generate comments dataset")
    # BUG COMMITS LOG DATASET GEN
    subparsers.add_parser("commits", parents=[period_parser, path_parser],
                          description="BUG COMMITS LOG DATASET GEN",
                          help="Generate commits log dataset")

    args = main_parser.parse_args()
    action = args.action

    if action and args.path:
      projects_path = os.path.join(args.path)

    if action == "bugfix":
      os.makedirs(os.path.join("dataset", "snapshot"), exist_ok=True)
      since_date = datetime.strptime(args.period[0], '%Y-%m-%d')
      to_date = datetime.strptime(args.period[1], '%Y-%m-%d')
      mine_BugFix(projects_path, since_date, to_date)

    if action == "changelog":
      os.makedirs(os.path.join("dataset", "changelog"), exist_ok=True)
      mine_Bugs_ChangeLog(projects_path)

    if action == "comments":
      os.makedirs(os.path.join("dataset", "comment-log"), exist_ok=True)
      mine_Bugs_CommentsLog(projects_path)

    if action == "commits":
      os.makedirs(os.path.join("dataset", "commit-log"), exist_ok=True)
      since_date = datetime.strptime(args.period[0], '%Y-%m-%d')
      to_date = datetime.strptime(args.period[1], '%Y-%m-%d')
      mine_Bugs_CommitsLog(projects_path, since_date, to_date)


if __name__ == "__main__":
    main()