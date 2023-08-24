from collections import Counter
from itertools import groupby

from utils import highlight
from word import Word


def grid(words: list[Word]) -> str:
    return ""


# def two_letter_list(words: list[Word]) -> str:
#     tll = [word.word[:2].upper() for word in words]
#     tll_count = Counter(tll)

#     tll_sort = [f"{letters}-{tll_count[letters]}" for letters in sorted(set(tll))]

#     letter = ""
#     pairs = []
#     for pair in tll_sort:
#         if pair[0] != letter:
#             pairs.append("\n")
#         pairs.append(pair)
#         letter = pair[0]

#     return " ".join(pairs)


def two_letter_list(words: list[Word]) -> str:
    two_letter_counts = Counter(word.word[:2].upper() for word in words)
    sorted_pairs = sorted(two_letter_counts.items())

    grouped_strings = [
        " ".join(f"{pair}-{count}" for pair, count in group)
        for _, group in groupby(sorted_pairs, key=lambda x: x[0][0])
    ]

    return "\n".join(grouped_strings)


def hints(words: list[Word], letters: str) -> str:
    center_letter, *outer_letters = letters.upper()
    highlighted_letters = " ".join([highlight(center_letter), *outer_letters])

    output = [
        f"Center letter is in {highlight('bold')}.\n",
        f"{highlighted_letters}\n",
        f"Words: {len(words)}, "
        f"Points: {sum(word.score for word in words)}, "
        f"Pangrams: {sum(word.is_pangram for word in words)}\n",
        two_letter_list(words),
    ]
    return "\n".join(output)
