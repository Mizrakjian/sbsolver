#!/usr/bin/env python
"""
SBSolver.py

This utility scrapes the NYT Spelling Bee web game and displays today's
possible words (found words that match the criteria of the game) and the
site's official answers.

-----

I wrote this when I couldn't complete the puzzle or find any solvers
online that could help with the game's unique format.  I saw early on that
the answers were embedded in the game site code, but created the word-finding
code anyway to to finish the project the way I originally planned.

Implemented 08/2023:
    Add feature to retrieve, display, and locally cache short word definitions.

Implemented 08/2023
    Use async io to improve definition fetch time.

TODO:
    Restructure project to split functionality and improve readability.
    Over time turn into a package?

Created on Wed Apr 27 2020
"""

import argparse
import asyncio
import json
from pathlib import Path
from textwrap import fill

import httpx
from bs4 import BeautifulSoup

SCRIPT_LOCATION = Path(__file__).parent
DATA_PATH = SCRIPT_LOCATION / "data"
WORDLIST_FILE = DATA_PATH / "word_list.txt"
DEFINITIONS_FILE = DATA_PATH / "definitions.json"
MAX_LINE_WIDTH = 72

# type for JSON word definitions
DefinitionMap = dict[str, dict[str, list[str]]]


def game_data() -> tuple[str, str, list[str]]:
    """Scrape Spelling Bee data and return game date, letters, and answers."""
    page = httpx.get("https://www.nytimes.com/puzzles/spelling-bee")
    soup = BeautifulSoup(page.content, "html.parser")

    data_tag = soup.find("script", string=lambda text: "window.gameData" in text)
    data = json.loads(data_tag.string.strip("window.gameData = "))["today"]  # type: ignore

    return data["displayDate"], "".join(data["validLetters"]), data["answers"]


def find_words(letters: str) -> list[str]:
    """
    Return a list of valid words formed from the given letters.

    A valid word must:
    - Be composed solely of the provided letters
    - Include the first letter from letters (the center letter)
    - Be at least 4 characters long
    """

    letter_set = set(letters)
    center_letter = letters[0]

    with open(WORDLIST_FILE) as word_list:
        return [
            word
            for line in word_list
            if set(word := line.strip()) <= letter_set
            if center_letter in word
            if len(word) >= 4
        ]


def score(word: str, letters: str) -> int:
    """
    Return int score of word using the following rules:
    - 4-letter words are 1 point
    - Longer words are 1 point per letter
    - Words using all puzzle letters are worth 7 additional points (pangram)
    """
    points = 1 if len(word) == 4 else len(word)
    points += 7 if set(word) == set(letters) else 0
    return points


def print_words(desc: str, words: list[str], letters: str) -> None:
    """Print count, description, and scored list of words. Display pangrams in bold and yellow."""
    bold_yellow, reset = "\033[1m\033[93m", "\033[0m"
    line_len = 0
    output = [f"\n{len(words)} {desc}:\n"]
    for word in words:
        scored = f"  {word} {score(word, letters)}"
        if line_len + len(scored) > MAX_LINE_WIDTH:
            output.append("\n")
            line_len = 0
        result = f"{bold_yellow}{scored}{reset}" if set(word) == set(letters) else scored
        output.append(result)
        line_len += len(scored)
    print("".join(output))


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

    async with httpx.AsyncClient() as client:
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


def print_definitions(words: list[str], lookup: DefinitionMap) -> None:
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
    for word in words:
        defined = lookup[word]["defs"]
        if len(defined) == 1:
            output = defined[0]
        else:
            output = (f"{i}. {d}" for i, d in enumerate(defined, 1))

        formatted = fill(
            "".join(output),
            width=MAX_LINE_WIDTH,
            initial_indent="  ",
            subsequent_indent="  ",
        )
        print(f"\n{word}\n{formatted}")


def main(show_definitions: bool = False):
    date, letters, answers = game_data()
    print(f"\nNYT Spelling Bee Solver — {date} Letters: {letters.capitalize()}")
    print_words("possible words found", find_words(letters), letters)
    print_words("official answers", answers, letters)

    defined_words = asyncio.run(get_definitions(answers))

    if show_definitions:
        print_definitions(answers, defined_words)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spelling Bee Solver")
    parser.add_argument("--define", action="store_true", help="Display definitions for answer words.")

    args = parser.parse_args()

    main(args.define)
