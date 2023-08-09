from json import loads
from typing import NamedTuple

from bs4 import BeautifulSoup
from httpx import get

from constants import GAME_URL


class GameData(NamedTuple):
    date: str
    letters: str
    answers: list[str]


def game_data() -> GameData:
    """Scrape Spelling Bee data and return game date, letters, and answers."""
    page = get(GAME_URL)
    soup = BeautifulSoup(page.content, "html.parser")
    tag = soup.find("script", string=lambda text: "window.gameData" in text)
    data = loads(tag.string.strip("window.gameData = "))["today"]  # type: ignore

    return GameData(
        date=data["displayDate"],
        letters="".join(data["validLetters"]),
        answers=data["answers"],
    )
