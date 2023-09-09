from core import MAX_LINE_WIDTH

from .utils import highlight
from .word import Word


def show_words(desc: str, words: list[Word]) -> str:
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
