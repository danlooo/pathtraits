import click
import inotify.adapters
import yaml
import re
import os
import pathlib
import logging

logger = logging.getLogger(__name__)

@click.group()
def main():
    pass

@main.command()
@click.argument("path", required=True)
def start(path):
    i = inotify.adapters.Inotify()
    i.add_watch(path)

    yaml_re = re.compile(r"\.(yaml|yml)$")
    for event in i.event_gen(yield_nones=False):
        (_, type_names, dir_path, filename) = event
        
        logger.debug(
            "PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(
              path, filename, type_names)
        )

        if not type_names.__contains__("IN_CLOSE_WRITE"):
            continue

        if yaml_re.search(filename):
            yml_path = os.path.join(dir_path, filename)
            with open(yml_path, "r") as f:
                yml_d = yaml.safe_load(f)
                if yml_d is None:
                    continue
                
                file_path =  re.sub(yaml_re, "", yml_path)
                if os.path.exists(file_path):
                    print(file_path, yml_d)

if __name__ == "__main__":
    main()