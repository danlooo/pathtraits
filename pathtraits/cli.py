import click
import logging
from pathtraits import scan, access

logger = logging.getLogger(__name__)


@click.group()
def main():
    pass


@main.command(help="Update database once, searches for all directories recursively.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=None,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
@click.option(
    "--include-files",
    flag_value=True,
    default=False,
    help="Also search for YAML sidecar files",
)
def batch(path, db_path, verbose, include_files):
    scan.batch(path, db_path, verbose, include_files)


@main.command(help="Update database continiously, watches for new or changed files.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=None,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
def watch(path, db_path, verbose):
    scan.watch(path, db_path, verbose)


@main.command(help="Get traits of a given path")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=None,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
def get(path, verbose):
    access.get(path, verbose)


if __name__ == "__main__":
    main()
