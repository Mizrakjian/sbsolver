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

TODO:
    Use async io to improve definition fetch times.

Created on Wed Apr 27 2020
"""

import argparse
import json
from pathlib import Path
from textwrap import fill

from bs4 import BeautifulSoup
from requests import get

SCRIPT_LOCATION = Path(__file__).parent
MAX_LINE_WIDTH = 72

# type for JSON word definitions
DefinitionMap = dict[str, dict[str, list[str]]]


def game_data() -> tuple[str, str, list[str]]:
    """Scrape Spelling Bee data and return game date, letters, and answers."""
    page = get("https://www.nytimes.com/puzzles/spelling-bee")
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
    wordlist_file = SCRIPT_LOCATION / "twl06.txt"

    with open(wordlist_file) as word_list:
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


def define(word: str) -> list[str]:
    """
    Fetch a list of definitions for a given word using the Datamuse API.

    Args:
    - word (str): The word for which definitions are to be fetched.

    Returns:
    - list[str]: A list containing the definitions for the word.
    """

    max_results = 4
    base_url = "https://api.datamuse.com/words"
    params = {
        "sp": word,
        "md": "d",
        "max": 1,
    }
    response = get(base_url, params=params)

    if response.status_code != 200:
        print(f"Error {response.status_code}: Unable to fetch data.")
        return []

    data = response.json()
    lookup = data[0].get("defs", ["<definition not found>"])
    return [item.replace("\t", ". ") for item in lookup[:max_results]]


def get_definitions(words: list[str]) -> DefinitionMap:
    """
    Fetch definitions for a list of words, checking and updating a local cache.

    For each word in the list, the function checks if its definition is
    already present in a local JSON file. If not, it fetches the definition
    using the Datamuse API and updates the JSON file.

    Args:
    - words (list[str]): A list of words for which definitions are to be fetched.

    Returns:
    - dict: A dictionary where the key is the word and the value is a dictionary
            with the key "defs" pointing to its definitions.
    """
    definitions_file = SCRIPT_LOCATION / "definitions.json"

    # Load existing definitions if the file exists
    if definitions_file.exists():
        with definitions_file.open("r") as f:
            defined_words = json.load(f)
    else:
        defined_words = {}

    for word in words:
        if word not in defined_words:
            defined_words[word] = {"defs": define(word)}

    # Update the JSON file with new definitions
    # Disable writing of definitions file so we always fetch from api
    # with definitions_file.open("w") as f:
    #     json.dump(defined_words, f, indent=4)

    return defined_words


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
    defined_words = get_definitions(answers)
    if show_definitions:
        print_definitions(answers, defined_words)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spelling Bee Solver")
    parser.add_argument("--define", action="store_true", help="Display definitions for answer words.")

    args = parser.parse_args()

    main(args.define)
