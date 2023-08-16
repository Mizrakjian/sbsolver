import asyncio
import json
import sqlite3
from textwrap import fill

from httpx import AsyncClient

from constants import DATAMUSE_URL, MAX_LINE_WIDTH, WORDS_DB

# type for API word definitions
DefinitionMap = dict[str, list[str]]


async def async_fetch_definitions(word: str) -> DefinitionMap:
    """Fetch and return a list of definitions for a given word from the Datamuse API."""

    params = {
        "sp": word,  # spelled-like query
        "md": "d",  # definitions metadata flag
        "max": 1,  # fetch one match only
    }
    async with AsyncClient() as client:
        response = await client.get(DATAMUSE_URL, params=params)

    data = response.json()
    if response.status_code != 200 or not data:
        print(f"  Unable to fetch data for {word} ({response.status_code=})")
        return {word: []}

    return {word: data[0].get("defs", [])}


async def async_batch_fetch_definitions(words: list[str]) -> DefinitionMap:
    """Fetch definitions for the provided list of words asynchronously."""
    batch = [async_fetch_definitions(word) for word in words]
    results = await asyncio.gather(*batch)
    return {
        word: defs
        for entry in results
        for word, defs in entry.items()
    }  # fmt: skip


def load_definitions(word_list: list[str]) -> DefinitionMap:
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

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

        definitions = {}
        for word, definition in cursor.fetchall():
            definitions.setdefault(word, []).append(definition)

    return definitions


def save_definitions(definitions: DefinitionMap) -> None:
    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        word_rows = []
        definition_rows = []

        for word, defs in definitions.items():
            cursor.execute("INSERT OR IGNORE INTO words (word) VALUES (?)", (word,))
            cursor.execute("SELECT word_id FROM words WHERE word = ?", (word,))
            word_id = cursor.fetchone()[0]
            word_rows.append((word,))
            for definition in defs:
                definition_rows.append((word_id, definition))

        cursor.executemany(
            "INSERT OR IGNORE INTO definitions (word_id, definition) VALUES (?, ?)", definition_rows
        )

        plural = "s" if len(word_rows) > 1 else ""
        print(f"\n{len(word_rows)} new word{plural} added:")
        print(" ", *[row[0] for row in word_rows])


def define_words(words: list[str]) -> DefinitionMap:
    """
    Define a list of words, checking and updating a local cache.

    For each word in the list, the function checks if its definition is
    already present in a local JSON file. If not, it fetches the definition
    using the Datamuse API and updates the JSON file.

    Args:
    - words (list[str]): The list of words to be defined.

    Returns:
    - dict: A dictionary where the key is the word and the value is a dictionary
            with the key "defs" pointing to its definitions.
    """
    defined = load_definitions(words)
    undefined = set(words) - set(defined.keys())

    if undefined:
        plural = "s" if len(undefined) > 1 else ""
        print(f"\nFetching {len(undefined)} new definition{plural}:")

        new_definitions = asyncio.run(async_batch_fetch_definitions(list(undefined)))
        defined |= new_definitions
        save_definitions(defined)

        print("  Done")

    return {word: defined[word] for word in words}


def print_definitions(words: DefinitionMap, max_entries: int = 4) -> None:
    """
    Display the definitions of words from a dictionary.

    The function prints each word in the dictionary, along with its definitions
    in a formatted manner.

    Args:
    - words (dict): A dictionary containing words and definitions to be displayed.
    - max_entries (int, optional): The maximum number of definitions per word to print.
      Defaults to 4.

    Returns:
    - None
    """
    for word, defs in words.items():
        entries = []
        for i, d in enumerate(defs[:max_entries], start=1):
            d = d.replace("\t", ". ")
            entries.append(f"{i}. {d}" if len(defs) > 1 else d)

        definition_text = "".join(entries) or "<definition not found>"

        definition = fill(
            definition_text,
            width=MAX_LINE_WIDTH,
            initial_indent="  ",
            subsequent_indent="  ",
        )

        print(f"\n{word}\n{definition}")
