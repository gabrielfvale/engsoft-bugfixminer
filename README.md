<h1 align='center'>
    <img src="https://ik.imagekit.io/dudaap/logobugfixminer_Yy0kuELHP.png">
</h1>

---

## 🧾Table of contents
- [About](#-About)
- [Requirements](#-Requirements)
- [Source code](#Source-code)
- [Install](#Install)

---

## 🔖About 
**Bugfix Miner** , given a period of time and a list of projects of Apache Software Foundation, it goes to JIRA in apache and search for all bug reports and resolved in that given period, extracts informations from the bug reports and save them in archives .csv. Besides that, Bugfix Miner search in the git repository of the given project for the commits that resolved those bugs.

---

### Requirements
 - Jira
 - Pydriller
 - nltk
 - pandas
 
 The list of dependencies is shown in ./requirements.txt


---

### Source code
```bash
    #Clone repository
    $ git clone https://github.com/gabrielfvale/engsoft-bugfixminer.git
    $ cd engsoft-bugfixminer.git


```

---

### Install

after you've cloned the repository, just use:
    > bugfixminer [opition] [period]
- options: bugfix, comments, commits, changelog
- period: yyyy-mm-dd
