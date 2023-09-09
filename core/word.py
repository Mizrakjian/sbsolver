from textwrap import fill
from typing import Iterable

from core import MAX_LINE_WIDTH

from .utils import highlight


class Word:
    """
    Represents a word with associated definitions, scoring, and pangram status.

    Attributes:
        text (str): The word in lowercase.
        definitions (list[str]): A list of definitions associated with the word.
        is_pangram (bool): True if the word uses all 7 puzzle letters, otherwise False.
        score (int): The score value of the word based on its length and pangram status.

    Methods:
        from_list(words: list[str]) -> list[Word]:
            Class method to create a list of Word objects from a list of word strings.

        calculate_score() -> int:
            Calculate the score of the word based on its length and pangram status.

        with_definitions(max_entries: int = 4) -> str:
            Return the word along with its wrapped, formatted definitions up to a specified limit.

        __repr__() -> str:
            Return a developer-friendly string representation of the Word object.

        __str__() -> str:
            Return a formatted string representation of the Word object with its definitions and score.

    Usage:
        word_obj = Word("example", ["a representative form", "a model"])
        print(word_obj)  # Outputs the word with definitions and score.
    """

    def __init__(self, word, definitions: list[str] | None = None):
        self.text = word.lower()
        self.definitions = definitions or []
        self.is_pangram = len(set(self.text)) == 7
        self.score = self.calculate_score()

    @classmethod
    def from_list(cls, words: Iterable[str]) -> list["Word"]:
        """Class method to return a list of Word objects from an iterable of word strings."""
        return [cls(word) for word in words]

    def calculate_score(self):
        """
        Return int score of word using the following rules:
        - 4-letter words are 1 point
        - Longer words are 1 point per letter
        - Words using all puzzle letters (pangrams) are worth 7 additional points
        """
        base_score = 1 if len(self.text) == 4 else len(self.text)
        pangram_bonus = 7 if self.is_pangram else 0
        return base_score + pangram_bonus

    def with_definitions(self, max_entries: int = 4) -> str:
        """
        Return the word and its wrapped, formatted definitions as a str.

        max_entries (int, optional): The maximum number of definitions to use. Defaults to 4.
        """
        entry_text = "".join(
            f"{i}. {d}" if len(self.definitions) > 1 else d
            for i, d in enumerate(self.definitions[:max_entries], start=1)
        ).replace("\t", ". ")

        definitions = fill(
            entry_text,
            width=MAX_LINE_WIDTH,
            initial_indent="  ",
            subsequent_indent="  ",
        )
        return f"{highlight(self.text) if self.is_pangram else self.text}\n{definitions}"

    def __repr__(self):
        return f"Word('{self.text}', definitions={self.definitions})"

    def __str__(self):
        return f"{self.with_definitions()}"

    def __lt__(self, other: "Word") -> bool:
        return self.text < other.text
