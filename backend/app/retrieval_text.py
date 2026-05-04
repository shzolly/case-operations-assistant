import re


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "has",
    "i",
    "in",
    "is",
    "it",
    "no",
    "of",
    "or",
    "should",
    "the",
    "to",
    "what",
    "when",
    "with",
}


def tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_PATTERN.findall(text)
        if token.lower() not in STOP_WORDS and len(token) > 1
    ]

