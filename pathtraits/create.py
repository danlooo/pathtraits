"""
Module for creating and populating yaml files
"""

import logging
import os
import platform
import pathlib
import subprocess
from datetime import datetime
from importlib.metadata import version
if platform.system() != "Windows":
    import grp
    import pwd
else:
    import getpass


logger = logging.getLogger(__name__)

def get_dust_metrics(path):
    """Calls dust to get size and file count."""
    # Check if dust is installed in the current environment
    if subprocess.run(["which", "dust"], capture_output=True, check=False).returncode != 0:
        return "N/A (dust not found)", "N/A"

    size_cmd = ["dust", "-s", "-c", "-b", path]
    inode_cmd = ["dust", "-s", "-c", "-b", "-i", path]
    size_out = subprocess.check_output(size_cmd, text=True).split()[0]
    inode_out = subprocess.check_output(inode_cmd, text=True).split()[0]
    return size_out, inode_out


def get_folder_context(path):
    """Retrieves owner, group, leader, and folder creation/change time."""
    path_obj = pathlib.Path(path)
    stat_info = path_obj.stat()

    # Folder Creation Time
    try:
        created_ts = stat_info.st_birthtime
    except AttributeError:
        created_ts = stat_info.st_ctime
    folder_origin = datetime.fromtimestamp(created_ts).strftime('%Y-%m-%d')

    if platform.system() != "Windows":
        owner = pwd.getpwuid(stat_info.st_uid).pw_name
        process_owner = pwd.getpwuid(os.getuid()).pw_name
        group = grp.getgrgid(stat_info.st_gid).gr_name
        leader = "Manual Entry Required"
    else:
        owner = getpass.getuser()
        process_owner = owner
        group = os.environ.get("USERDOMAIN", "LocalGroup")
        leader = "N/A"

    return owner, process_owner, group, leader, folder_origin


def generate_metadata(path, needed_until:str=None, overwrite:bool = False, verbose: bool = False):
    """
    Generates metadata.yaml. 

    :param needed_until: Until when this folder is expected to be needed, 
        can be a string in format '%Y-%m-%d' (e.g., "2026-12-31" ) or None.
    :param overwrite: Overwrite if metadata already exists? Default False
    :param verbose: enable verbose logging
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    file_path = os.path.join(path, "meta.yml")
    if os.path.exists(file_path) and not overwrite:
        logger.debug("Skipping: '%s' already exists.", file_path)
        logger.debug("Use 'overwrite=True' if you want to replace it.")
        return

    owner, process_owner, group, leader, folder_created = get_folder_context(path)
    size, inodes = get_dust_metrics(path)

    template = f"""# identification:
pathtraits_version: {version("pathtraits")}
yml_created_date: {datetime.now().strftime('%Y-%m-%d')}
yml_created_by: "{process_owner}"
folder_created_date: {folder_created}
folder_owner: "{owner}"
folder_owner_group: "{group}"
folder_owner_group_lead: “{leader}"
folder_no.files: {inodes}
folder_size: {size}
folder_needed_until: "{needed_until}"

# --- OPTIONAL FIELDS ---
# project: "..."
# tags: []
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(template)

    logger.debug("Successfully generated template at: %s", file_path)
