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

Todo:
    Add feature to retrieve, display, and locally cache short word definitions.

Created on Wed Apr 27 2020
"""

import argparse
from json import loads
from pathlib import Path
from textwrap import fill

from bs4 import BeautifulSoup
from requests import get


def game_data() -> tuple[str, str, list[str]]:
    """Scrape Spelling Bee data and return game date, letters, and answers."""
    page = get("https://www.nytimes.com/puzzles/spelling-bee")
    soup = BeautifulSoup(page.content, "html.parser")

    data_tag = soup.find("script", string=lambda text: "window.gameData" in text)
    data = loads(data_tag.string.strip("window.gameData = "))["today"]  # type: ignore

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
    wordlist_file = "twl06.txt"
    wordlist_path = Path(__file__).parent / wordlist_file

    with open(wordlist_path) as word_list:
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
    max_line_len = 70
    line_len = 0
    output = [f"\n{len(words)} {desc}:\n"]
    for word in words:
        scored = f"  {word} {score(word, letters)}"
        if line_len + len(scored) > max_line_len:
            output.append("\n")
            line_len = 0
        result = f"{bold_yellow}{scored}{reset}" if set(word) == set(letters) else scored
        output.append(result)
        line_len += len(scored)
    print("".join(output))


def get_definitions(word: str) -> list[str]:
    """Fetch synonyms for a given word using the Datamuse API."""

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


def print_definitions(words: list[str]) -> None:
    max_line_len = 68
    for word in words:
        print(f"\n{word}")
        output = []
        definitions = get_definitions(word)
        if len(definitions) == 1:
            output = f"{definitions[0]}"
        else:
            for i, d in enumerate(get_definitions(word), 1):
                output.append(f"{i}. {d}\n")
        print(
            fill(
                "".join(output),
                width=max_line_len,
                initial_indent="  ",
                subsequent_indent="  ",
            )
        )


def main(define: bool = False):
    date, letters, answers = game_data()
    print(f"\nNYT Spelling Bee Solver — {date} Letters: {letters.capitalize()}")
    print_words("possible words found", find_words(letters), letters)
    print_words("official answers", answers, letters)
    if define:
        print_definitions(answers)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get word definitions.")
    parser.add_argument("--define", action="store_true", help="Display definitions of the word.")

    args = parser.parse_args()

    main(args.define)
