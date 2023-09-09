import logging
from json import loads
from typing import NamedTuple

from bs4 import BeautifulSoup
from httpx import get

from .word import Word

GAME_URL = "https://www.nytimes.com/puzzles/spelling-bee"
SCRIPT_NAME = "window.gameData = "

log = logging.getLogger(__name__)


class GameData(NamedTuple):
    date: str
    letters: str
    answers: list[Word]


def game_data() -> list[GameData]:
    """Scrape Spelling Bee data and return list of GameData entries in descending date order."""

    log.info("Fetch game data")

    try:
        page = get(GAME_URL)
        soup = BeautifulSoup(page.content, "html.parser")
        tag = soup.find("script", string=lambda text: SCRIPT_NAME in text)
        data = loads(tag.string.strip(SCRIPT_NAME))  # type: ignore
    except Exception as e:
        error = f"Scrape failed with: {e}"
        log.error(error)
        print(error)
        exit(1)

    return [
        GameData(
            date=game["displayDate"],
            letters="".join(game["validLetters"]),
            answers=Word.from_list(game["answers"]),
        )
        for week in ("thisWeek", "lastWeek")
        for game in reversed(data["pastPuzzles"][week])
    ]
