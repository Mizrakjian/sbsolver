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

import logging

from core import VERSION, definitions, hints, logging_config, parse_args, scrape, show_words, utils, word

logger = logging.getLogger(__name__)


def main():
    logging_config.setup_logging()

    args = parse_args.parse_args()

    logger.info(f"Start v{VERSION} | {args.formatted}")

    game_history = scrape.game_data()
    count = len(game_history) - 1

    days_ago = args.past
    if days_ago is None or not (0 <= days_ago <= count):
        print(f"There are {count} available past games. The oldest is from {game_history[-1].date}.")
        logger.info(f"End v{VERSION} | {args.formatted}")
        exit()

    puzzle = game_history[days_ago]
    answers = word.Word.from_list(puzzle.answers)

    print(f"\n{utils.highlight('Spelling Bee Solver')} — {puzzle.date}\n")
    print(hints.hints(answers, puzzle.letters), "\n")

    if args.answers:
        print(show_words.show_words("official answers", answers), "\n")

    definitions.define(answers)

    if args.define:
        for answer_word in answers:
            print(answer_word.with_definitions(), "\n")

    if args.stats:
        utils.show_db_stats()

    logger.info(f"End v{VERSION} | {args.formatted}")


if __name__ == "__main__":
    main()
