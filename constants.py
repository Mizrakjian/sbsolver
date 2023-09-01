from pathlib import Path

VERSION = "1.5.1"

GAME_URL = "https://www.nytimes.com/puzzles/spelling-bee"
WORDLIST_URL = "https://www.wordgamedictionary.com/twl06/download/twl06.txt"
DATAMUSE_URL = "https://api.datamuse.com/words"

DATA_PATH = Path(__file__).parent / "data"
WORDS_DB = DATA_PATH / "words.db"

MAX_LINE_WIDTH = 72
