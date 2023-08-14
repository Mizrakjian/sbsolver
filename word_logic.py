from pathlib import Path

from constants import ADDENDUM_FILE, MAX_LINE_WIDTH, WORDLIST_FILE


def find_words(letters: str) -> list[str]:
    """
    Return a list of valid words formed from the given letters.

    A valid word must:
    - Be composed solely of the provided letters
    - Include the first letter from letters (the center letter)
    - Be at least 4 characters long
    """

    words = word_list()
    letter_set = set(letters)
    center_letter = letters[0]

    return [
        word
        for word in words
        if set(word) <= letter_set
        if center_letter in word
        if len(word) >= 4
    ]  # fmt: skip


def words_from(word_file: Path) -> set[str]:
    """Return set of words from a word file."""
    if word_file.exists():
        with open(word_file) as file:
            return set(line.strip() for line in file)
    else:
        return set()


def word_list() -> list[str]:
    """Return sorted list of known words by combining words from wordlist and addendum files."""
    all_words = set()
    for file in [WORDLIST_FILE, ADDENDUM_FILE]:
        all_words |= words_from(file)
    return sorted(all_words)


def update_word_list(words: set[str]) -> None:
    with open(ADDENDUM_FILE, "a") as file:
        for word in words:
            file.write(f"{word}\n")

    plural = "s" if len(words) > 1 else ""
    print(f"\n{len(words)} new word{plural} added:")
    print(" ", *words)


def is_pangram(word: str) -> bool:
    """Words using all 7 puzzle letters are pangrams."""
    return len(set(word)) == 7


def score(word: str) -> int:
    """
    Return int score of word using the following rules:
    - 4-letter words are 1 point
    - Longer words are 1 point per letter
    - Words using all puzzle letters (pangrams) are worth 7 additional points
    """
    points = 1 if len(word) == 4 else len(word)
    points += 7 if is_pangram(word) else 0
    return points


def print_words(desc: str, words: list[str]) -> None:
    """Print count, description, and scored list of words. Highlight pangrams in bold yellow."""

    highlight = lambda word: f"\033[1m\033[93m{word}\033[0m"
    line_len = 0
    output = [f"\n{len(words)} {desc}:\n"]
    for word in words:
        scored = f"  {word} {score(word)}"
        if line_len + len(scored) > MAX_LINE_WIDTH:
            output.append("\n")
            line_len = 0
        result = f"{highlight(scored)}" if is_pangram(word) else scored
        output.append(result)
        line_len += len(scored)
    print("".join(output))
