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
from typing import List, Tuple

from bs4 import BeautifulSoup
from requests import get


def game_data() -> Tuple[str, str, List[str]]:
    """Scrape Spelling Bee data and return game date, letters, and answers."""
    page = get("https://www.nytimes.com/puzzles/spelling-bee")
    soup = BeautifulSoup(page.content, "html.parser")
    data = loads(soup.script.string.strip("window.gameData = "))["today"]
    return data["displayDate"], "".join(data["validLetters"]), data["answers"]


def find_words(letters: str) -> List[str]:
    """Return list of found valid words using letters."""
    # Valid words are made from set(letters), contain letters[0], and have length >= 4.
    words = []
    with open(f"{Path(__file__).parent}\\twl06.txt") as word_list:
        for word in word_list:
            word = word.strip()
            if set(word).issubset(letters) and letters[0] in word and len(word) >= 4:
                words.append(word)
    return words


def score(word: str, letters: str) -> str:
    """Return string of word and its score."""
    # 4-letter words are 1 point, longer words are 1 point per letter.
    points = 1 if len(word) == 4 else len(word)
    # Words using all puzzle letters are worth 7 additional points.
    points += 7 if set(word) == set(letters) else 0
    return f"  {word} {points}"


def print_words(desc: str, words: List[str], letters: str) -> None:
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
