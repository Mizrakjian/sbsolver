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
  *  Add feature to retrieve, display, and locally cache short word definitions.
  *  Use async io to improve definition fetch time.
  *  Restructure project to modularize functionality and improve readability.

TODO:
    Over time turn into a package?

Created on Wed Apr 27 2020
"""

from argparse import ArgumentParser

from definitions import define_words, print_definitions
from game_data import game_data
from word_logic import find_words, print_words, update_addendum


def main(show_definitions: bool = False):
    date, letters, answers = game_data()[-1]  # [-1] to keep new game_data() from breaking main()
    found_words = find_words(letters)

    print(f"\nNYT Spelling Bee Solver — {date} Letters: {letters.capitalize()}")
    print_words("possible words found", found_words)
    print_words("official answers", answers)

    defined_words = define_words(answers)
    new_words = set(answers) - set(found_words)
    if new_words:
        update_addendum(new_words)

    if show_definitions:
        print_definitions(defined_words)


if __name__ == "__main__":
    parser = ArgumentParser(description="Spelling Bee Solver")
    parser.add_argument(
        "-d",
        "--define",
        action="store_true",
        help="Display definitions for answer words.",
    )
    args = parser.parse_args()

    main(args.define)
