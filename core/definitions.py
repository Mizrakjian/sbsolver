import asyncio
import logging
import sqlite3

from httpx import AsyncClient

from constants import DATAMUSE_URL, WORDS_DB
from utils import create_words_db
from word import Word

logger = logging.getLogger(__name__)


async def async_batch_fetch(words: list[Word]) -> None:
    """Fetch definitions for the provided list of Word objects asynchronously."""

    async def async_fetch_defs(client: AsyncClient, word: Word) -> None:
        """Fetch and set the definition for a given Word object using the Datamuse API."""
        params = {
            "sp": word.text,  # spelled-like query
            "md": "d",  # definitions metadata flag
            "max": 1,  # fetch one match only
        }
        response = await client.get(url=DATAMUSE_URL, params=params)
        data = response.json()

        if response.status_code == 200 and data and (defs := data[0].get("defs")):
            word.definitions = defs
        else:
            logger.warning(f"'{word.text}' data not found, status code:{response.status_code}")
            word.definitions = ["<definition not found>"]

    logging.info(f"Definitions to fetch: {len(words)}")

    async with AsyncClient() as client:
        batch = (async_fetch_defs(client, w) for w in words)
        await asyncio.gather(*batch)


def load_definitions(words: list[Word]) -> None:
    """Load definitions from WORDS_DB into the list of Word objects. Creates the database if missing."""

    if not WORDS_DB.exists():
        logger.warning(f"{WORDS_DB} file missing")
        create_words_db()

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
            logger.info(f"Add {words_added} word(s) to database")

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
    from an outside API, updates each definitions attribute in the
    Word list, and finally adds new definitions to the db.

    Args:
    - words (list[Word]): The list of Word objects to be defined.
    """

    load_definitions(words)
    undefined = [word for word in words if not word.definitions]

    if undefined:
        asyncio.run(async_batch_fetch(undefined))
        save_definitions(undefined)
