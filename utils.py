import sqlite3

import requests

from constants import WORDLIST_URL, WORDS_DB


def fetch_wordlist():
    """Return list of words from wordgamedictionary.com's TWL06 scrabble word list."""

    response = requests.get(WORDLIST_URL)
    word_list = response.text.split("\n")
    return [(word.strip(),) for word in word_list[2:]]


def create_db_tables(db_path):
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
            definition_id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER,
            definition TEXT,
            FOREIGN KEY(word_id) REFERENCES words(word_id)
        )"""
        )


def populate_words_table(db_path, word_list):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany("INSERT OR IGNORE INTO words (word) VALUES (?)", word_list)
    print(f"Populated words table with words from the word list.")


def create_words_db():
    word_list = fetch_wordlist()
    create_db_tables(WORDS_DB)
    populate_words_table(WORDS_DB, word_list)


def get_random_words_with_definitions(count=5):
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        # Get the random words that have definitions
        cursor.execute(
            """
            SELECT w.word
            FROM words w
            INNER JOIN definitions d ON d.word_id = w.word_id
            GROUP BY w.word
            ORDER BY RANDOM() LIMIT ?
            """,
            (count,),
        )
        words = [row[0] for row in cursor.fetchall()]

        # Get the definitions for the random words
        for word in words:
            cursor.execute(
                """
                SELECT GROUP_CONCAT(definition, ' ') AS definitions
                FROM (
                    SELECT d.definition
                    FROM definitions d
                    INNER JOIN words w ON d.word_id = w.word_id
                    WHERE w.word = ?
                    LIMIT 4
                )
                """,
                (word,),
            )
            definitions = cursor.fetchone()[0].replace("\t", ". ")
            print(f"\n{word}:\n  {definitions}")


def show_db_stats() -> None:
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM words")
        total_words = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT word_id) FROM definitions")
        defined_words = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM definitions")
        total_definitions = cursor.fetchone()[0]

    print(
        f"\n{WORDS_DB} stats:\n"
        f"  {total_words = }\n"
        f"  {defined_words = }\n"
        f"  {total_definitions = }\n"
    )


if __name__ == "__main__":
    show_db_stats()
    get_random_words_with_definitions(5)


# import asyncio
# from pathlib import Path
# from definitions import async_batch_fetch_definitions, load_definitions, save_definitions

# def update_definitions_json():
#     local_defs = load_definitions()
#     api_defs = asyncio.run(async_batch_fetch_definitions(list(local_defs)))

#     for word, defs in api_defs.items():
#         if local_defs[word]["defs"] != defs["defs"] and defs["defs"]:
#             print(f"Updating local definition for {word}.")
#             local_defs[word]["defs"] = defs["defs"]

#     save_definitions(local_defs)

# def show_undefined_words():
#     local_defs = load_definitions()
#     for word, defs in local_defs.items():
#         if not defs["defs"]:
#             print(word)

# def populate_definitions_table(db_path, definitions):
#     with sqlite3.connect(db_path) as conn:
#         cursor = conn.cursor()

#         # Get a mapping of word to word_id
#         cursor.execute("SELECT word, word_id FROM words")
#         word_to_id = {row[0]: row[1] for row in cursor.fetchall()}

#         # Prepare the definitions data for insertion
#         insert_data = []
#         for word, data in definitions.items():
#             word_id = word_to_id[word]
#             for definition in data["defs"]:
#                 insert_data.append((word_id, definition))

#         # Insert the definitions into the definitions table
#         cursor.executemany(
#             "INSERT OR IGNORE INTO definitions (word_id, definition) VALUES (?, ?)", insert_data
#         )

#     print("Imported definitions from JSON file into the definitions table.")
