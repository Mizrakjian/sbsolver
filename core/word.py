from typing import Iterable

from .utils import highlight, wrap_text


class Word:
    """
    Represent a word with its associated definitions, score, and pangram status.

    Attributes / properties:
        text (str): The word in lowercase.
        definitions (list[str]): A list of definitions associated with the word.
        is_pangram (bool): True if the word uses all 7 puzzle letters.
        score (int): The score of the word based on its length and pangram status.

    Methods:
        from_list(words: list[str]) -> list[Word]:
            Class method to create a list of Word objects from a list of strings.

        with_definitions(max_entries: int = 4) -> str:
            Return the word along with its wrapped, formatted definitions up to a specified limit.

    Usage:
        word_obj = Word("example", ["a representative form", "a model"])
        print(word_obj)  # Outputs the word with definitions and score.
    """

    def __init__(self, text: str, definitions: list[str] | None = None):
        self.text = text.lower()
        self.definitions = definitions or []
        self._is_pangram = len(set(self.text)) == 7
        self._score = self._calc_score()

    def _calc_score(self) -> int:
        """
        Return word score based on length and pangram status.
        - 4-letter words are 1 point
        - Longer words are 1 point per letter
        - Pangrams are worth 7 additional points
        """
        base_score = 1 if len(self.text) == 4 else len(self.text)
        pangram_bonus = 7 if self.is_pangram else 0
        return base_score + pangram_bonus

    @property
    def is_pangram(self) -> bool:
        return self._is_pangram

    @property
    def score(self) -> int:
        return self._score

    @classmethod
    def from_list(cls, words: Iterable[str]) -> list["Word"]:
        """Return a list of Word objects from an iterable of word strings."""
        return [cls(word) for word in words]

    def with_definitions(self, max_entries: int = 4) -> str:
        """
        Return word text with wrapped, formatted definitions as a str.

        max_entries (int, optional): The maximum number of definitions to use. Defaults to 4.
        """
        entry_text = "".join(
            f"{i}. {d}" if len(self.definitions) > 1 else d
            for i, d in enumerate(self.definitions[:max_entries], start=1)
        ).replace("\t", ". ")

        definitions = wrap_text(entry_text)
        return f"{highlight(self.text) if self.is_pangram else self.text}\n{definitions}"

    def __repr__(self):
        return f"Word('{self.text}', definitions={self.definitions})"

    def __str__(self):
        return (
            f"{self.text}, "
            f"{len(self.definitions)} definition(s), "
            f"score = {self.score}{', pangram' if self.is_pangram else ''}"
        )

    def __lt__(self, other: "Word") -> bool:
        return self.text < other.text
