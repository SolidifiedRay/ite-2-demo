#!/usr/bin/env python3
"""TUF Client Example"""

# Copyright 2012 - 2017, New York University and the TUF contributors
# SPDX-License-Identifier: MIT OR Apache-2.0

import argparse
import logging
import os
import sys
import traceback
from hashlib import sha256
from pathlib import Path
from urllib import request

from tuf.api.exceptions import DownloadError, RepositoryError
from tuf.ngclient.updater import Updater

# constants
DOWNLOAD_DIR = "./downloads"
CLIENT_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
METADATA_URL = "http://127.0.0.1:8080/"
TARGET_URL = "http://127.0.0.1:8000/"

def build_metadata_dir(base_url: str) -> str:
    """build a unique and reproducible directory name for the repository url"""
    name = sha256(base_url.encode()).hexdigest()[:8]
    # TODO: Make this not windows hostile?
    return f"{Path.home()}/.local/share/tuf-example/{name}"

def download(target: str) -> bool:
    """
    Download the target file using ``ngclient`` Updater.

    The Updater refreshes the top-level metadata, get the target information,
    verifies if the target is already cached, and in case it is not cached,
    downloads the target file.

    Returns:
        A boolean indicating if process was successful
    """
    metadata_dir = build_metadata_dir(METADATA_URL)

    if not os.path.isfile(f"{metadata_dir}/root.json"):
        print(
            "Download root metadata to "
            f"{metadata_dir}/root.json"
        )
        return False

    print(f"Using trusted root in {metadata_dir}")

    if not os.path.isdir(DOWNLOAD_DIR):
        os.mkdir(DOWNLOAD_DIR)

    try:
        updater = Updater(
            metadata_dir=metadata_dir,
            metadata_base_url=METADATA_URL,
            target_base_url=TARGET_URL,
            target_dir=DOWNLOAD_DIR,
        )
        updater.refresh()

        info = updater.get_targetinfo(target)

        if info is None:
            print(f"Target {target} not found")
            return True

        path = updater.find_cached_target(info)
        if path:
            print(f"Target is available in {path}")
            return True

        path = updater.download_target(info)
        print(f"Target downloaded and available in {path}")

    except (OSError, RepositoryError, DownloadError) as e:
        print(f"Failed to download target {target}: {e}")
        if logging.root.level < logging.ERROR:
            traceback.print_exc()
        return False

    return True


def main():
    """Main TUF Client Example function"""

    client_args = argparse.ArgumentParser(description="TUF Client Example")

    # Global arguments
    client_args.add_argument(
        "-v",
        "--verbose",
        help="Output verbosity level (-v, -vv, ...)",
        action="count",
        default=0,
    )

    # Sub commands
    sub_command = client_args.add_subparsers(dest="sub_command")

    # Download
    download_parser = sub_command.add_parser(
        "download",
        help="Download a target file",
    )

    download_parser.add_argument(
        "target",
        metavar="TARGET",
        help="Target file",
    )

    command_args = client_args.parse_args()

    if command_args.verbose == 0:
        loglevel = logging.ERROR
    elif command_args.verbose == 1:
        loglevel = logging.WARNING
    elif command_args.verbose == 2:
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG

    logging.basicConfig(level=loglevel)

    # initialize the TUF Client Example infrastructure
    if command_args.sub_command == "download":
        if not download(command_args.target):
            return f"Failed to download {command_args.target}"
    else:
        client_args.print_help()


if __name__ == "__main__":
    sys.exit(main())
