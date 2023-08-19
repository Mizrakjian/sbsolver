import asyncio
import sqlite3
from textwrap import fill

from httpx import AsyncClient

from constants import DATAMUSE_URL, MAX_LINE_WIDTH, WORDS_DB

# type for API word definitions
DefinitionMap = dict[str, list[str]]


async def async_fetch_defs(word: str) -> DefinitionMap:
    """Fetch and return a list of definitions for a given word from the Datamuse API."""

    params = {
        "sp": word,  # spelled-like query
        "md": "d",  # definitions metadata flag
        "max": 1,  # fetch one match only
    }
    async with AsyncClient() as client:
        response = await client.get(url=DATAMUSE_URL, params=params)

    data = response.json()
    if response.status_code != 200 or not data:
        print(f"  Unable to fetch data for {word} ({response.status_code=})")
        return {word: []}

    return {word: data[0].get("defs", [])}


async def async_batch_fetch(words: set[str]) -> DefinitionMap:
    """Fetch definitions for the provided set of words asynchronously."""
    batch = [async_fetch_defs(word) for word in words]
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
    new_words = []
    defs_count = 0

    with sqlite3.connect(WORDS_DB) as conn:
        cursor = conn.cursor()

        for word, defs in definitions.items():
            cursor.execute("INSERT OR IGNORE INTO words (word) VALUES (?)", (word,))
            if cursor.rowcount:
                new_words.append(word)

            cursor.execute("SELECT word_id FROM words WHERE word = ?", (word,))
            (word_id,) = cursor.fetchone()

            defs_list = [(word_id, definition) for definition in defs]
            cursor.executemany(
                "INSERT OR IGNORE INTO definitions (word_id, definition) VALUES (?, ?)",
                defs_list,
            )
            if cursor.rowcount:
                defs_count += 1

        plural = lambda count: "s" if count != 1 else ""
        word_count = len(new_words)
        if word_count:
            print(f"\n{word_count} new word{plural(word_count)} added:")
            print(" ", *new_words)
        if defs_count:
            print(f"\nFetched {defs_count} new definition{plural(defs_count)}.")


def define_words(words: list[str]) -> DefinitionMap:
    """
    Define a list of words, checking and updating a local db.

    For each word in the list, the function checks if its definition is
    already present in a local db. If not, it fetches the definition
    using the Datamuse API and updates the db.

    Args:
    - words (list[str]): The list of words to be defined.

    Returns:
    - dict: A dictionary where the key is a word and the value
            is a list of its definitions.
    """
    defined = load_definitions(words)
    undefined = set(words) - set(defined.keys())

    if undefined:
        api_definitions = asyncio.run(async_batch_fetch(undefined))
        defined |= api_definitions
        save_definitions(defined)

    # Return definitions in same order as input
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
