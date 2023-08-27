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

from definitions import define
from game_data import game_data
from hints import hints
from utils import show_db_stats
from word import Word
from word_logic import show_words


def parse_args():
    parser = ArgumentParser(description="Spelling Bee Solver")

    parser.add_argument(
        "-a",
        "--answers",
        action="store_true",
        help="show the puzzle answers",
    )
    parser.add_argument(
        "-d",
        "--define",
        action="store_true",
        help="show answer definitions",
    )
    parser.add_argument(
        "-p",
        "--past",
        metavar="n",
        nargs="?",
        type=int,
        const=None,
        default=0,
        help="Load puzzle from [n] days ago - show available days if [n] is omitted",
    )
    parser.add_argument(
        "-s",
        "--stats",
        action="store_true",
        help="show database stats",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    game_history = game_data()
    count = len(game_history) - 1

    days_ago = args.past
    if days_ago is None or not (0 <= days_ago <= count):
        print(f"There are {count} available past games. The oldest is from {game_history[-1].date}.")
        exit()

    puzzle = game_history[days_ago]
    answers = Word.from_list(puzzle.answers)

    print(f"\nSpelling Bee Solver — {puzzle.date}\n")
    print(hints(answers, puzzle.letters), "\n")

    if args.answers:
        print(show_words("official answers", answers), "\n")

    define(answers)

    if args.define:
        for word in answers:
            print(word.with_definitions(), "\n")

    if args.stats:
        show_db_stats()


if __name__ == "__main__":
    main()
