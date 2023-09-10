import logging
import sqlite3
from datetime import datetime
from textwrap import fill

import httpx

from core import MAX_LINE_WIDTH, WORDS_DB

WORDLIST_URL = "https://www.wordgamedictionary.com/twl06/download/twl06.txt"

log = logging.getLogger(__name__)


def highlight(text: str) -> str:
    """Return highlighted text with ANSI codes for bold and yellow."""
    return f"\033[1;93m{text}\033[0m"


def wrap_text(text: str, indent: int = 2) -> str:
    """Return MAX_LINE_WIDTH wrapped and indented text."""

    return fill(
        text,
        width=MAX_LINE_WIDTH,
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
    )


def fetch_wordlist() -> list[tuple[str]]:
    """Return list of words from wordgamedictionary.com's TWL06 scrabble word list."""

    log.info(f"Fetch wordlist")

    response = httpx.get(WORDLIST_URL)
    word_list = response.text.split("\n")
    return [(word.strip(),) for word in word_list[2:]]


def create_db():
    if not WORDS_DB.parent.exists():
        log.info(f"Create directory: {WORDS_DB.parent}")
        WORDS_DB.parent.mkdir(parents=True, exist_ok=True)

    log.info("Create database")

    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE words (
                word_id INTEGER PRIMARY KEY,
                word TEXT UNIQUE NOT NULL
            )
            """
        )
        cursor.execute("CREATE INDEX word_index ON words(word);")

        cursor.execute(
            """
            CREATE TABLE definitions (
                word_id INTEGER NOT NULL,
                definition TEXT NOT NULL,
                UNIQUE (word_id, definition),
                FOREIGN KEY(word_id) REFERENCES words(word_id)
            )
            """
        )
        cursor.execute("CREATE INDEX word_id_index ON definitions(word_id);")

        cursor.execute(
            """
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY NOT NULL,
                value INTEGER NOT NULL
            )
            """
        )


def populate_db(word_list):
    log.info(f"Add {len(word_list)} words to database")

    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()
        cursor.executemany("INSERT OR IGNORE INTO words (word) VALUES (?)", word_list)

        # Get the highest word_id
        cursor.execute("SELECT MAX(word_id) FROM words")
        (max_word_id,) = cursor.fetchone()
        creation_date = int(datetime.now().timestamp())

        cursor.executemany(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            [("creation_date", creation_date), ("initial_words_count", max_word_id)],
        )


def create_words_db():
    create_db()
    word_list = fetch_wordlist()
    populate_db(word_list)


def show_new_words():
    from .definitions import define
    from .word import Word

    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM metadata WHERE key = 'initial_words_count'")
        initial_words = cursor.fetchone()
        cursor.execute("SELECT word FROM words WHERE word_id > ?", initial_words)
        new_words = Word.from_list(word for (word,) in cursor)
        define(new_words)
        for word in new_words:
            print(word.with_definitions(), "\n")


def show_db_stats() -> None:
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT key, value FROM metadata")
        metadata = dict(cursor)
        creation_date = datetime.fromtimestamp(metadata["creation_date"])
        initial_words_count = metadata["initial_words_count"]

        cursor.execute(
            """
            SELECT COUNT(*) FROM words
            UNION ALL
            SELECT COUNT(DISTINCT word_id) FROM definitions
            UNION ALL
            SELECT COUNT(*) FROM definitions
            """
        )
        total_words, defined_words, total_definitions = (item for (item,) in cursor)

        cursor.execute("SELECT word FROM words WHERE word_id > ?", (initial_words_count,))
        new_words = [w for (w,) in cursor]

        cursor.execute(
            """
            SELECT w.word
            FROM words w
            JOIN definitions d ON d.word_id = w.word_id
            WHERE d.definition = "<definition not found>"
            """
        )
        defs_not_found = [w for (w,) in cursor]

    added_words = wrap_text(" ".join(new_words), indent=4)
    bad_defs = wrap_text(" ".join(defs_not_found), indent=4)

    print(
        f"Stats for {WORDS_DB}:\n"
        f"  Creation date: {creation_date}\n"
        f"  Total words: {total_words}\n"
        f"  Added words: {len(new_words)}\n{added_words}\n"
        f"  Empty definitions: {len(defs_not_found)}\n{bad_defs}\n"
        f"  Defined words: {defined_words}\n"
        f"  Total definitions: {total_definitions}\n"
    )


if __name__ == "__main__":
    show_db_stats()
    show_new_words()

    with sqlite3.connect(WORDS_DB) as conn:
        conn.execute("VACUUM")
