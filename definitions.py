import asyncio
import json
from textwrap import fill

from httpx import AsyncClient

from constants import DEFINITIONS_FILE, MAX_LINE_WIDTH

# type for JSON word definitions
DefinitionMap = dict[str, dict[str, list[str]]]


async def define(word: str, max_results: int = 4) -> list[str]:
    """
    Fetch a list of definitions for a given word from the Datamuse API.

    Args:
    - word (str): The word to define.
    - max_results (int, optional): Maximum number of definitions to return. Defaults to 4.

    Returns:
    - list[str]: A list of definitions.
    """

    base_url = "https://api.datamuse.com/words"
    params = {
        "sp": word,
        "md": "d",
        "max": 1,  # Fetch only one matching word from Datamuse
    }

    async with AsyncClient() as client:
        response = await client.get(base_url, params=params)

    if response.status_code != 200:
        print(f"Error {response.status_code}: Unable to fetch data for {word}.")
        return []

    lookup = response.json()[0].get("defs", ["<definition not found>"])

    return [item.replace("\t", ". ") for item in lookup[:max_results]]


def load_json_definitions() -> DefinitionMap:
    if DEFINITIONS_FILE.exists():
        with DEFINITIONS_FILE.open("r") as f:
            return json.load(f)
    return {}


def save_json_definitions(definitions: DefinitionMap) -> None:
    with DEFINITIONS_FILE.open("w") as f:
        json.dump(definitions, f, indent=4)


async def get_definitions(words: list[str]) -> DefinitionMap:
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
    defined = load_json_definitions()
    undefined = set(words) - set(defined.keys())

    if undefined:
        print(f"\nFetching {len(undefined)} new definitions... ", end="")

        results = await asyncio.gather(*map(define, undefined))

        print("Done")

        new_definitions = {w: {"defs": r} for w, r in zip(undefined, results)}
        defined.update(new_definitions)
        save_json_definitions(defined)

    return {word: defined[word] for word in words}


def define_words(words: list[str]) -> DefinitionMap:
    """Fetch definitions for the provided list of words asynchronously."""
    return asyncio.run(get_definitions(words))


def print_definitions(lookup: DefinitionMap) -> None:
    """
    Display the definitions of words from a lookup dictionary.

    For each word in the list, the function fetches its definitions from
    the lookup dictionary and prints them in a formatted manner.

    Args:
    - words (list[str]): A list of words for which definitions are to be displayed.
    - lookup (dict): A dictionary containing the definitions of words.

    Returns:
    - None
    """
    for word, defs in lookup.items():
        defined = defs["defs"]

        output = (
            f"{i}. {d}" if len(defined) > 1 else d
            for i, d in enumerate(defined, 1)
        )  # fmt: skip

        definition = fill(
            "".join(output),
            width=MAX_LINE_WIDTH,
            initial_indent="  ",
            subsequent_indent="  ",
        )

        print(f"\n{word}\n{definition}")
