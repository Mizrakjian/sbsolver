import asyncio
import json
from textwrap import fill

from httpx import AsyncClient

from constants import DATAMUSE_URL, DEFINITIONS_FILE, MAX_LINE_WIDTH

# type for API word definitions
DefinitionMap = dict[str, dict[str, list[str]]]


async def async_fetch_definitions(word: str) -> DefinitionMap:
    """Fetch and return a list of definitions for a given word from the Datamuse API."""

    base_url = DATAMUSE_URL
    params = {
        "sp": word,
        "md": "d",
        "max": 1,  # Fetch only one matching word
    }

    async with AsyncClient() as client:
        response = await client.get(base_url, params=params)

    if response.status_code != 200:
        print(f"Error {response.status_code}: Unable to fetch data for {word}.")
        return {}

    return {word: {"defs": response.json()[0].get("defs", [])}}


async def async_batch_fetch_definitions(words: list[str]) -> DefinitionMap:
    """Fetch definitions for the provided list of words asynchronously."""
    batch = [async_fetch_definitions(word) for word in words]
    results = await asyncio.gather(*batch)
    return {word: defs for entry in results for word, defs in entry.items()}


def load_definitions() -> DefinitionMap:
    if DEFINITIONS_FILE.exists():
        with DEFINITIONS_FILE.open("r") as f:
            return json.load(f)
    return {}


def save_definitions(definitions: DefinitionMap) -> None:
    with DEFINITIONS_FILE.open("w") as f:
        json.dump(definitions, f, indent=4)


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
    defined = load_definitions()
    undefined = set(words) - set(defined.keys())

    if undefined:
        print(f"\nFetching {len(undefined)} new definitions... ", end="")

        new_definitions = asyncio.run(async_batch_fetch_definitions(list(undefined)))

        print("Done")

        defined |= new_definitions
        save_definitions(defined)

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
        defs = defs["defs"][:max_entries]
        entries = []
        for i, d in enumerate(defs, start=1):
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


def update_definitions_json():
    local_defs = load_definitions()
    api_defs = asyncio.run(async_batch_fetch_definitions(list(local_defs)))

    for word, defs in api_defs.items():
        if local_defs[word]["defs"] != defs["defs"]:
            print(f"Updating local definition for {word}.")
            local_defs[word]["defs"] = defs["defs"]

    save_definitions(local_defs)
