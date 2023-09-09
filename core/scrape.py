import logging
from json import loads
from typing import NamedTuple

from bs4 import BeautifulSoup
from httpx import get

from .word import Word

GAME_URL = "https://www.nytimes.com/puzzles/spelling-bee"

logger = logging.getLogger(__name__)


class GameData(NamedTuple):
    date: str
    letters: str
    answers: list[Word]


def game_data() -> list[GameData]:
    """Scrape Spelling Bee data and return list of GameData entries in reverse order."""

    logger.info("Fetch game data")

    page = get(GAME_URL)
    soup = BeautifulSoup(page.content, "html.parser")
    tag = soup.find("script", string=lambda text: "window.gameData" in text)
    data = loads(tag.string.strip("window.gameData = "))  # type: ignore

    return [
        GameData(
            date=game["displayDate"],
            letters="".join(game["validLetters"]),
            answers=Word.from_list(game["answers"]),
        )
        for week in ("lastWeek", "thisWeek")
        for game in data["pastPuzzles"][week]
    ][::-1]