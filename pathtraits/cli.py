import click
import logging
from pathtraits import scan, access
import os

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("PATHTRAITS_DB_PATH", os.path.expanduser("~/.pathtraits.db"))


@click.group()
def main():
    pass


@main.command(help="Update database once, searches for all directories recursively.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=DB_PATH,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
def batch(path, db_path, verbose):
    scan.batch(path, db_path, verbose)


@main.command(help="Update database continiously, watches for new or changed files.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=DB_PATH,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
def watch(path, db_path, verbose):
    scan.watch(path, db_path, verbose)


@main.command(help="Get traits of a given path")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=DB_PATH,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
def get(path, db_path, verbose):
    access.get(path, db_path, verbose)


if __name__ == "__main__":
    main()
