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
from utils import show_db_stats
from word_logic import find_words, print_words, update_word_list


def parse_args():
    parser = ArgumentParser(description="Spelling Bee Solver")
    parser.add_argument(
        "-s",
        "--show",
        action="store_true",
        help="Show definitions for official answer words.",
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        help="Use game letters and words from X days ago. 0 for today, 1 for yesterday, etc.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print statistics about the words database.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    game_history = game_data()

    days_ago = args.days or 0
    if days_ago < 0 or days_ago >= len(game_history):
        print(f"{days_ago} is an invalid choice. The data only goes back {len(game_history)-1} days.")
        exit()

    date, letters, answers = game_history[days_ago]
    found_words = find_words(letters)

    print(f"\nNYT Spelling Bee Solver — {date} Letters: {letters.capitalize()}")
    print_words("possible words found", found_words)
    print_words("official answers", answers)

    new_words = set(answers) - set(found_words)
    if new_words:
        update_word_list(new_words)

    defined_words = define_words(answers)

    if args.show:
        print_definitions(defined_words)

    if args.stats:
        show_db_stats()


if __name__ == "__main__":
    main()
