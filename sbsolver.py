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

from json import loads
from pathlib import Path

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
    - Contain at least 4 characters
    """

    center_letter = letters[0]
    letter_set = set(letters)
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


def score(word: str, letters: str) -> str:
    """
    Return string of word and its score.
    - 4-letter words are 1 point
    - Longer words are 1 point per letter
    - Words using all puzzle letters are worth 7 additional points
    """
    points = 1 if len(word) == 4 else len(word)
    points += 7 if set(word) == set(letters) else 0
    return f"  {word} {points}"


def print_words(desc: str, words: list[str], letters: str) -> None:
    """Print count, description, and scored list of words."""
    output = [f"\n{len(words)} {desc}:\n"]
    line_len = 0
    for word in words:
        scored = score(word, letters)
        if line_len + len(scored) > 68:
            output.append("\n")
            line_len = 0
        output.append(scored)
        line_len += len(scored)
    print("".join(output))


if __name__ == "__main__":
    date, letters, answers = game_data()
    print(f"\nNYT Spelling Bee Solver — {date} Letters: {letters.capitalize()}")
    print_words("possible words found", find_words(letters), letters)
    print_words("official answers", answers, letters)
