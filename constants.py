from pathlib import Path

GAME_URL = "https://www.nytimes.com/puzzles/spelling-bee"
DATAMUSE_URL = "https://api.datamuse.com/words"

DATA_PATH = Path(__file__).parent / "data"
WORDLIST_FILE = DATA_PATH / "word_list.txt"
ADDENDUM_FILE = DATA_PATH / "addendum.txt"
DEFINITIONS_FILE = DATA_PATH / "definitions.json"

MAX_LINE_WIDTH = 72
