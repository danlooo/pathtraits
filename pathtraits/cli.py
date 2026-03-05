"""
Module of the command line interface to pathtraits
"""

import logging
import os
import click
from pathtraits import scan, access, create as _create

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("PATHTRAITS_DB_PATH", os.path.expanduser("~/.pathtraits.db"))


@click.group()
def main():
    """
    pathtraits: Annotate files and directories using YAML sidecar files
    """


@main.command()
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
    Deletes existing database to ensure its synced with sidecar metadata files.
    """
    scan.batch(path, db_path, exclude_regex, verbose)


@main.command()
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
    """
    scan.watch(path, db_path, verbose)


@main.command()
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
    """
    access.get(path, db_path, verbose)


@main.command()
@click.argument("query_str", required=True)
@click.option(
    "--db-path",
    default=DB_PATH,
    type=click.Path(file_okay=True, dir_okay=False),
)
def query(query_str, db_path):
    """
    Get paths of given traits

    Enter QUERY_STR in SQLite3 where statement format,
    e.g. "score_REAL>1" to get all paths having a numerical score >1.
    """
    access.query(query_str, db_path)


@main.command()
@click.argument(
    "path", required=True, type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--needed-until",
    "-nu",
    default=None,
    help="Optional account termination date (YYYY-MM-DD)",
)
@click.option(
    "--overwrite",
    "-o",
    is_flag=True,
    default=False,
    help="Overwrite existing metadata.",
)
@click.option("-v", "--verbose", is_flag=True, default=False)
def create(path, needed_until, overwrite, verbose):
    """
    Update database once, searches for all directories recursively.
    """
    _create.generate_metadata(path, needed_until, overwrite, verbose)


if __name__ == "__main__":
    main()
