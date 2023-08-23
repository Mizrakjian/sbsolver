import asyncio
import sqlite3

from httpx import AsyncClient

from constants import DATAMUSE_URL, WORDS_DB
from word import Word


async def async_fetch_defs(word: Word) -> None:
    """Fetch and set the definitions for a given Word object from the Datamuse API."""
    params = {
        "sp": word.word,  # spelled-like query
        "md": "d",  # definitions metadata flag
        "max": 1,  # fetch one match only
    }
    async with AsyncClient() as client:
        response = await client.get(url=DATAMUSE_URL, params=params)

    data = response.json()
    if response.status_code == 200 and data and (defs := data[0].get("defs")):
        word.definitions = defs
    else:
        print(f"  Unable to fetch data for {word.word} ({response.status_code=})")
        word.definitions = ["<definition not found>"]


async def async_batch_fetch(words: list[Word]) -> None:
    """Fetch definitions for the provided list of Word objects asynchronously."""
    batch = (async_fetch_defs(word) for word in words)
    await asyncio.gather(*batch)


def load_definitions(words: list[Word]) -> None:
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        word_list = [word.word for word in words]
        placeholders = ", ".join("?" * len(word_list))
        cursor.execute(
            f"""
            SELECT words.word, definitions.definition
            FROM words
            INNER JOIN definitions ON words.word_id = definitions.word_id
            WHERE words.word IN ({placeholders})
            """,
            word_list,
        )

        definition_map = {}
        for word, definition in cursor.fetchall():
            definition_map.setdefault(word, []).append(definition)

        for word in words:
            word.definitions = definition_map[word.word]


def save_definitions(words: list[Word]) -> None:
    new_words = []
    defs_count = 0

    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        for word in words:
            cursor.execute("INSERT OR IGNORE INTO words (word) VALUES (?)", (word.word,))
            cursor.execute("SELECT word_id FROM words WHERE word = ?", (word.word,))
            word_id = cursor.fetchone()[0]
            if cursor.rowcount:
                new_words.append(word.word)

            defs_list = [(word_id, definition) for definition in word.definitions]
            cursor.executemany(
                "INSERT OR IGNORE INTO definitions (word_id, definition) VALUES (?, ?)",
                defs_list,
            )
            defs_count += cursor.rowcount

        plural = lambda count: "s" if count != 1 else ""
        word_count = len(new_words)
        if word_count:
            print(f"\n{word_count} new word{plural(word_count)} added:")
            print(" ", *new_words)
        if defs_count:
            print(f"\nFetched {defs_count} new definition{plural(defs_count)}.")


def define(words: list[Word]) -> None:
    """
    Define a list of words, checking and updating the local db.

    For each word in the list, the function checks if its definition is
    already present in the local db. If not, it fetches the definition
    using the Datamuse API and updates the db.

    Args:
    - word_objects (list[Word]): The list of Word objects to be defined.
    """
    load_definitions(words)
    undefined = [word for word in words if not word.definitions]

    if undefined:
        asyncio.run(async_batch_fetch(undefined))
        save_definitions(undefined)
