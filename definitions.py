import asyncio
import sqlite3

from httpx import AsyncClient

from constants import DATAMUSE_URL, WORDS_DB
from word import Word


async def async_fetch_defs(word: Word) -> None:
    """Fetch and set the definitions for a given Word object from the Datamuse API."""
    params = {
        "sp": word.text,  # spelled-like query
        "md": "d",  # definitions metadata flag
        "max": 1,  # fetch one match only
    }
    async with AsyncClient() as client:
        response = await client.get(url=DATAMUSE_URL, params=params)

    data = response.json()
    if response.status_code == 200 and data and (defs := data[0].get("defs")):
        word.definitions = defs
    else:
        print(f"  Unable to fetch data for {word.text} ({response.status_code=})")
        word.definitions = ["<definition not found>"]


async def async_batch_fetch(words: list[Word]) -> None:
    """Fetch definitions for the provided list of Word objects asynchronously."""
    batch = (async_fetch_defs(word) for word in words)
    await asyncio.gather(*batch)


def load_definitions(words: list[Word]) -> None:
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        word_list = [word.text for word in words]
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
            word.definitions = definition_map.get(word.text, [])


def save_definitions(words: list[Word]) -> None:
    new_words = []
    new_defs = 0

    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        for word in words:
            cursor.execute("INSERT OR IGNORE INTO words (word) VALUES (?)", (word.text,))
            if cursor.rowcount:
                new_words.append(word.text)

            defs = ((d, word.text) for d in word.definitions)
            cursor.executemany(
                """
                INSERT OR IGNORE INTO definitions (word_id, definition)
                SELECT w.word_id, ?
                FROM words w
                WHERE w.word = ?
                """,
                defs,
            )
            if cursor.rowcount:
                new_defs += 1

        plural = lambda count: "s" if count != 1 else ""
        if word_count := len(new_words):
            print(f"\n{word_count} new word{plural(word_count)} added:")
            print(" ", *new_words)
        if new_defs:
            print(f"\nFetched {new_defs} new definition{plural(new_defs)}.")


def define(words: list[Word]) -> None:
    """
    Define a list of words and update the local db.

    For each word in the list, the function checks if its definition is
    already present in the local db. If not, it fetches the definition
    using the Datamuse API, updates each definitions attribute in the
    Word list, and finally adds new definitions to the db.

    Args:
    - word_objects (list[Word]): The list of Word objects to be defined.
    """
    load_definitions(words)
    undefined = [word for word in words if not word.definitions]

    if undefined:
        asyncio.run(async_batch_fetch(undefined))
        save_definitions(undefined)
