"""
hints.py: functions to display Spelling Bee puzzle statistics and hints.
"""
from collections import Counter, defaultdict
from itertools import groupby

from utils import highlight
from word import Word


def grid(words: list[Word]) -> str:
    """
    Generate a grid of word counts by initial letter and length.

    Example:
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
    header = f"     {fmt_join(lengths)}  ∑"
    footer = f"  ∑: {fmt_join(counts)} {len(words):>2}"

    # Count (first letter, word length) pair frequency
    pairs = Counter((w.text[0], len(w.text)) for w in words)
    by_letter = defaultdict(dict)
    for (letter, length), count in sorted(pairs.items()):
        by_letter[letter][length] = count

    rows = []
    for letter, length_counts in by_letter.items():
        counts = " ".join(f"{length_counts.get(l, '-'):>2}" for l in lengths)
        total = f"{sum(length_counts.values()):>2}"
        rows.append(f"  {highlight(letter.upper())}: {counts} {highlight(total)}")

    return "\n".join([highlight(header), *rows, highlight(footer)])


def two_letter_list(words: list[Word]) -> str:
    """Return word counts grouped by their first two letters."""

    two_letter_counts = Counter(w.text[:2].upper() for w in words)
    sorted_pairs = sorted(two_letter_counts.items())
    first_letter = lambda x: x[0][0]

    groups = [
        "  " + " ".join(f"{letters}-{count}" for letters, count in group)
        for _, group in groupby(sorted_pairs, key=first_letter)
    ]
    return "\n".join(["Two letter list:", *groups])


def pangrams(words: list[Word]) -> str:
    """
    Return the count of pangrams and perfect pangrams.

    A pangram uses all puzzle letters.
    A perfect pangram uses all puzzle letters but only once each.
    """

    pangram_list = [word.text for word in words if word.is_pangram]
    pangram_count = len(pangram_list)
    perfect_count = sum(len(p) == 7 for p in pangram_list)
    if pangram_count == perfect_count == 1:
        perfect = " (Perfect)"
    elif pangram_count > 1 and perfect_count:
        perfect = f" ({perfect_count} Perfect)"
    else:
        perfect = ""
    return f"{pangram_count}{perfect}"


def hints(words: list[Word], letters: str) -> str:
    """Provide hints and statistics for the given words and puzzle letters."""

    center, *outers = letters.upper()
    puzzle_letters = " ".join([highlight(center), *outers])
    count = len(words)
    score = sum(w.score for w in words)
    bingo = " Bingo," if len({w.text[0] for w in words}) == 7 else ""

    output = [
        f"\nLetters: {puzzle_letters}",
        f"Words: {count}, Points: {score},{bingo} Pangrams: {pangrams(words)}",
        grid(words),
        two_letter_list(words),
    ]
    return "\n\n".join(output)
