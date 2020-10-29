import re
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk import FreqDist
from nltk.tokenize import RegexpTokenizer

TOP_MOST_FREQUENT_WORDS = 1000

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
