"""
Module of the command line interface to pathtraits
"""

import logging
import os
import click
from pathtraits import scan, access

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("PATHTRAITS_DB_PATH", os.path.expanduser("~/.pathtraits.db"))


@click.group()
def main():
    """
    pathtraits: Annotate files and directories using YAML sidecar files
    """


@main.command(help="Update database once, searches for all directories recursively.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=DB_PATH,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option(
    "--exclude-regex",
    default=None,
)
@click.option("-v", "--verbose", flag_value=True, default=False)
def batch(path, db_path, exclude_regex, verbose):
    """
    Update database once, searches for all directories recursively.

    :param path: path to scan in batch mode recursively
    :param db_path: path to the database
    :param exclude_regex: exclue file paths matching this regex
    :param verbose: enable verbose logging
    """
    scan.batch(path, db_path, exclude_regex, verbose)


@main.command(help="Update database continiously, watches for new or changed files.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=DB_PATH,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
def watch(path, db_path, verbose):
    """
    Update database continiously, watches for new or changed files.

    :param path: path to watch recursively
    :param db_path: path to the database
    :param verbose: enable verbose logging
    """
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
    """
    Get traits of a given path

    :param path: path to get traits for
    :param db_path: path to the database
    :param verbose: enable verbose logging
    """
    access.get(path, db_path, verbose)


if __name__ == "__main__":
    main()
