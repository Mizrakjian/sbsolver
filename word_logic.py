import sqlite3

from constants import MAX_LINE_WIDTH, WORDS_DB
from utils import create_words_db
from word import Word


def find_words(letters: str) -> list[Word]:
    """
    Return a list of valid words formed from the given letters.

    A valid word must:
    - Be composed solely of the provided letters
    - Include the first letter from letters (the center letter)
    - Be at least 4 characters long
    """

    center_letter = letters[0]
    words = word_list(
        includes=center_letter,
        min_length=4,
    )
    letter_set = set(letters)

    return [Word(word) for word in words if set(word) <= letter_set]


def word_list(*, includes: str, min_length: int) -> list[str]:
    """
    Return a list of words from the words database that:
    * contain the includes letter.
    * are at least min_length characters long.
    """
    if not WORDS_DB.exists():
        create_words_db()

    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT word
            FROM words
            WHERE LENGTH(word) >= ? AND word LIKE ?
            """,
            (min_length, f"%{includes}%"),
        )
        return [word for (word,) in cursor.fetchall()]


def print_words(desc: str, words: list[Word]) -> None:
    """Print count, description, and scored list of words. Highlight pangrams in bold yellow."""

    highlight = lambda word: f"\033[1m\033[93m{word}\033[0m"
    line_len = 0
    output = [f"\n{len(words)} {desc}:\n"]
    for word in words:
        scored = f"  {word.word} {word.score}"
        if line_len + len(scored) > MAX_LINE_WIDTH:
            output.append("\n")
            line_len = 0
        result = f"{highlight(scored)}" if word.is_pangram else scored
        output.append(result)
        line_len += len(scored)
    print("".join(output))
