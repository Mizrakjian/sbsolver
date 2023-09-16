from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser(description="Spelling Bee Solver")

    parser.add_argument(
        "-a",
        "--answers",
        action="store_true",
        help="show the puzzle answers",
    )
    parser.add_argument(
        "-d",
        "--define",
        action="store_true",
        help="show answer definitions",
    )
    parser.add_argument(
        "--hints",
        action="store_true",
        help="show list of hints",
    )
    parser.add_argument(
        "-p",
        "--past",
        metavar="n",
        nargs="?",
        type=int,
        const=None,
        default=0,
        help="Load puzzle from [n] days ago - show available days if [n] is omitted",
    )
    parser.add_argument(
        "-s",
        "--stats",
        action="store_true",
        help="show database stats",
    )
    args = parser.parse_args()

    args.formatted = ", ".join(f"{key}={value}" for key, value in vars(args).items())

    return args
