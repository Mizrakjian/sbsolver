"""
show.py: functions to display Spelling Bee puzzle statistics, hints, and words.
"""
import random
from collections import Counter, defaultdict
from itertools import groupby
from textwrap import fill

from core import MAX_LINE_WIDTH

from .utils import highlight, ital
from .word import Word


def grid(words: list[Word]) -> str:
    """
    Generate a grid of word counts by initial letter and length.

    Example output:
            3  4  5  6  Σ
        A:  1  -  1  -  2
        B:  1  -  -  1  2
        C:  1  1  -  -  2
        D:  1  -  -  -  1
        Σ:  4  1  1  1  7
    """
    # Count word length frequency
    length_count = Counter(len(w.text) for w in words)
    lengths, counts = zip(*sorted(length_count.items()))

    fmt_join = lambda items: " ".join(f"{i:>2}" for i in items)
    header = highlight(f"     {fmt_join(lengths)}  ∑")
    footer = highlight(f"  ∑: {fmt_join(counts)} {ital(len(words))}")

    # Count (first letter, word length) pair frequency
    pairs = Counter((w.text[0], len(w.text)) for w in words)
    by_letter = defaultdict(dict)
    for (letter, length), count in sorted(pairs.items()):
        by_letter[letter][length] = count

    rows = []
    for letter, length_counts in by_letter.items():
        cells = (length_counts.get(l, "-") for l in lengths)
        total = f"{sum(length_counts.values()):>2}"
        rows.append(f"  {highlight(letter.upper())}: {fmt_join(cells)} {highlight(total)}")

    return "\n".join([header, *rows, footer])


def two_letter_list(words: list[Word]) -> str:
    """Return counts of words by their first two letters, grouped by first letter."""

    two_letter_counts = Counter(w.text[:2].upper() for w in words)
    sorted_pairs = sorted(two_letter_counts.items())
    first_letter = lambda x: x[0][0]

    groups = [
        f"  {' '.join(f'{pair}-{count}' for pair, count in group)}"
        for _, group in groupby(sorted_pairs, key=first_letter)
    ]
    return "\n".join(["Two letter list:", *groups])


def pangrams(words: list[Word]) -> str:
    """
    Return the count of pangrams and perfect pangrams.

    Pangrams use all 7 puzzle letters at least once.
    Perfect pangrams are 7 letters long.
    """

    pangram_list = [w.text for w in words if w.is_pangram]
    pangram_count = len(pangram_list)
    perfect_count = sum(len(p) == 7 for p in pangram_list)

    perfect = ""
    if perfect_count:
        count = f"{perfect_count} " if pangram_count > 1 else ""
        perfect = f" ({count}Perfect)"

    return f"{pangram_count}{perfect}"


def hints(words: list[Word], letters: str) -> str:
    """Provide hints and statistics for the given words and puzzle letters."""

    center, *outers = letters.upper()
    puzzle_letters = " ".join([highlight(center), *outers])
    count = len(words)
    score = sum(w.score for w in words)
    # Set bingo when all seven puzzle letters are used to start a word.
    bingo = ", Bingo" if len({w.text[0] for w in words}) == 7 else ""

    output = [
        f"Letters: {puzzle_letters}",
        f"Words: {count}, Points: {score}, Pangrams: {pangrams(words)}{bingo}",
        grid(words),
        two_letter_list(words),
    ]
    return "\n\n".join(output)


def definition_hints(words: list[Word]) -> str:
    """
    Generate hints for each word, sorted by the word's text.

    Each hint will display the first two letters, the length of the word,
    and a random definition that doesn't contain the word itself.
    """
    hints = []
    for word in sorted(words):
        # Choose a random definition that doesn't contain the word itself
        valid_definitions = [d for d in word.definitions if word.text not in d]
        if valid_definitions:
            _, hint = random.choice(valid_definitions).split("\t")
        else:
            hint = "No definition available without the word itself."

        pair = word.text[:2].upper()
        entry = f"{pair}{len(word.text):>2} {hint}"

        hints.append(fill(entry, MAX_LINE_WIDTH, subsequent_indent=" " * 5))

    return "\n".join(hints)


def words(desc: str, words: list[Word]) -> str:
    """Return count, description, and scored list of words. Highlight pangrams in bold yellow."""

    line_len = 0
    output = [f"{len(words)} {desc}:\n"]
    for word in words:
        scored = f"  {word.text} {word.score}"
        if line_len + len(scored) > MAX_LINE_WIDTH:
            output.append("\n")
            line_len = 0
        result = f"{highlight(scored)}" if word.is_pangram else scored
        output.append(result)
        line_len += len(scored)
    return "".join(output)


def definitions(words: list[Word]) -> str:
    """Return string of word texts and definitions separated by \n\n."""
    return "\n\n".join(w.with_definitions() for w in words)
