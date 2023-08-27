import asyncio
import sqlite3

from httpx import AsyncClient

from constants import DATAMUSE_URL, WORDS_DB
from utils import create_words_db
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
    """Load definitions from WORDS_DB into the list of Word objects."""
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        lookup = {word.text: word for word in words}
        placeholders = ", ".join("?" * len(lookup))

        cursor.execute(
            f"""
            SELECT words.word, definitions.definition
            FROM words
            INNER JOIN definitions ON words.word_id = definitions.word_id
            WHERE words.word IN ({placeholders})
            """,
            list(lookup.keys()),
        )
        for word_text, definition in cursor:
            lookup[word_text].definitions.append(definition)


def save_definitions(words: list[Word]) -> None:
    """Save new words and/or definitions from the list of Word objects to WORDS_DB."""
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        cursor.executemany(
            "INSERT OR IGNORE INTO words (word) VALUES (?)",
            [(word.text,) for word in words],
        )
        if words_added := cursor.rowcount:
            print(f"Words added: {words_added}\n")

        cursor.executemany(
            """
            INSERT OR IGNORE INTO definitions (word_id, definition)
            SELECT w.word_id, ?
            FROM words w
            WHERE w.word = ?
            """,
            [(d, w.text) for w in words for d in w.definitions],
        )


def define(words: list[Word]) -> None:
    """
    Define a list of words and update the local db.

    For each word in the list, the function checks if its definition is
    already present in the local db. If not, it fetches the definition
    using the Datamuse API, updates each definitions attribute in the
    Word list, and finally adds new definitions to the db.

    Also creates the database if it isn't found.

    Args:
    - words (list[Word]): The list of Word objects to be defined.
    """
    if not WORDS_DB.exists():
        create_words_db()

    load_definitions(words)
    undefined = [word for word in words if not word.definitions]

    if undefined:
        print(f"Definitions to fetch: {len(undefined)}")
        asyncio.run(async_batch_fetch(undefined))
        print("  done\n")
        save_definitions(undefined)
