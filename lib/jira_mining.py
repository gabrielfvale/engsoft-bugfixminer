import pandas

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