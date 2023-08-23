import sqlite3
from datetime import datetime
from textwrap import fill

import requests

from constants import MAX_LINE_WIDTH, WORDLIST_URL, WORDS_DB
from word import Word


def fetch_wordlist() -> list[tuple[str]]:
    """Return list of words from wordgamedictionary.com's TWL06 scrabble word list."""

    response = requests.get(WORDLIST_URL)
    word_list = response.text.split("\n")
    return [(word.strip(),) for word in word_list[2:]]


def create_db(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE words (
                word_id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE
            )"""
        )
        cursor.execute(
            """
            CREATE TABLE definitions (
                word_id INTEGER,
                definition TEXT,
                UNIQUE (word_id, definition),
                FOREIGN KEY(word_id) REFERENCES words(word_id)
            )"""
        )
        cursor.execute(
            """
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value INTEGER
            )"""
        )


def populate_db(db_path, word_list):
    with sqlite3.connect(db_path) as conn:
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
    print(f"{WORDS_DB} file missing.\nCreating new database.")
    create_db(WORDS_DB)
    word_list = fetch_wordlist()
    populate_db(WORDS_DB, word_list)
    print(f"Populated database with {len(word_list)} words from wordgamedictionary.com.")


def show_new_words():
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM metadata WHERE key = 'initial_words_count'")
        initial_words = cursor.fetchone()
        cursor.execute("SELECT word FROM words WHERE word_id > ?", initial_words)
        new_words = cursor.fetchall()

        for (word,) in new_words:
            cursor.execute(
                """
                SELECT d.definition
                FROM definitions d
                INNER JOIN words w ON d.word_id = w.word_id
                WHERE w.word = ?
                """,
                (word,),
            )
            definitions = [definition for definition, in cursor.fetchall()]
            print(Word(word, definitions).with_definitions())


def show_db_stats() -> None:
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM metadata WHERE key = ?", ("creation_date",))
        (creation_date,) = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM words")
        (total_words,) = cursor.fetchone()

        cursor.execute("SELECT value FROM metadata WHERE key = 'initial_words_count'")
        (initial_words_count,) = cursor.fetchone()
        cursor.execute("SELECT word FROM words WHERE word_id > ?", (initial_words_count,))
        new_words = cursor.fetchall()

        cursor.execute(
            """
        SELECT w.word
        FROM words w
        INNER JOIN definitions d ON d.word_id = w.word_id
        WHERE d.definition = "<definition not found>"
        """
        )
        defs_not_found = cursor.fetchall()

        cursor.execute("SELECT COUNT(DISTINCT word_id) FROM definitions")
        (defined_words,) = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM definitions")
        (total_definitions,) = cursor.fetchone()

    added_words = fill(
        " ".join(word for (word,) in new_words),
        width=MAX_LINE_WIDTH,
        initial_indent="    ",
        subsequent_indent="    ",
    )
    bad_defs = fill(
        " ".join(word for (word,) in defs_not_found),
        width=MAX_LINE_WIDTH,
        initial_indent="    ",
        subsequent_indent="    ",
    )

    print(
        f"\nStats for {WORDS_DB}:\n"
        f"  Creation date: {datetime.fromtimestamp(creation_date)}\n"
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
