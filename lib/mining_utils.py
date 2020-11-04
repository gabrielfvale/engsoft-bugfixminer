import re
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk import FreqDist
from nltk.tokenize import RegexpTokenizer
import nltk

nltk.download("stopwords")
nltk.download("wordnet")

TOP_MOST_FREQUENT_WORDS = 1000

# ===========================Mining utility code=========================== #


def filter_top_frequent_words(text: str) -> str:

    """Filters the top frequent words (NLP) in a text string.

    From a text string, tokenize and match the words to a group, filters
    words and adds them to a most common words list

    Args:
        project: The path of the project CSV.
    
    Returns:
        A string containing pairs of frequent words.
    """

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
                         + ":"
                         + str(top_word[1])
                         for top_word in top_words])

    return text


def has_Source_Extension(file_name: str) -> bool:

    """Checks if a file contains common programming language extensions.

    Args:
        file_name: The name of the file to check.
    
    Returns:
        A boolean representing if wether or not the file has a useful extension.
    """

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


def is_Test(file_path: str) -> bool:

    """Checks if a file categorizes as a test.

    Args:
        file_path: The path of the file to check.
    
    Returns:
        A boolean representing if wether or not the file is a test.
    """

    test_clues = ["/test/", "test/", "/test", "/tests/", "tests/", "/tests"]
    for clue in test_clues:
        if(clue in file_path):
            return True
    return False


def extract_Keys(message: str) -> list:

    """Extracts keys from a message string.

    Args:
        message: The string to gather the keys.
    
    Returns:
        A list of the keys found.
    """

    keys = []

    if(message is None):
        return keys

    for key in re.findall(r"[A-Z0-9]{2,}-\d+", message):
        keys.append(key)

    return keys


def is_Valid_Key(message: str) -> bool:

    """Tries to match a message key through a RegEx.

    Args:
        message: The message to check.
    
    Returns:
        A boolean if the message passed the RegEx test.
    """

    if(message is None):
        return False

    if(re.match(r"[A-Z0-9]{2,}-\d+", message)):
        return True
    return False
