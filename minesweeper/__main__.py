import argparse

from . import application


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a game of minesweeper"
    )
    parser.add_argument(
        '-r', '--rows',
        required=False,
        default=10,
        type=int,
        help="Number of rows in the field"
    )
    parser.add_argument(
        '-c', '--cols',
        required=False,
        default=10,
        type=int,
        help="Number of columns in the field"
    )
    parser.add_argument(
        '-m', '--ratio',
        required=False,
        default=0.25,
        type=float,
        help="Number from 0.0 to 1.0 indicating what portion of the field "
             "should be mined."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    app = application.create_app(args.rows, args.cols, args.ratio)
    app.run()


if __name__ == "__main__":
    main()
