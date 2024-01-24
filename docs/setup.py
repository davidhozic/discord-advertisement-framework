"""
Script that setups the environment before build.
"""

from pathlib import Path
from argparse import ArgumentParser

import runpy
import os
import glob
import shutil
import json
import re


parse = ArgumentParser()
parse.add_argument("--clean", action="store_true", default=False, help="If given, it will only clean instead of copy and run")
parse.add_argument("--start-dir", default="./", dest="start_dir", help="Where to start looking for dep_local.json")
args = parse.parse_args()


CLEAN_ARG: bool = args.clean
START_DIR_ARG: str = args.start_dir

# Work relatively to the setup script location
os.chdir(os.path.dirname(__file__))


def strip_leading_dots(files: list[str]):
    return [re.sub(r'\.\.\/', '', f) for f in files]


for path, dirs, files in os.walk(START_DIR_ARG):
    for file in files:
        if file == "dep_local.json":
            file = os.path.join(path, file)
            # Copy files
            setup_file_data: dict = None
            with open(file, 'r', encoding="utf-8") as setup_file:
                setup_file_data = json.load(setup_file)

            # While copying change to dep-files cwd
            cwd = os.getcwd()
            os.chdir(os.path.abspath(os.path.dirname(file)))

            for rule in setup_file_data["copy"]:
                src_path, dst_path = Path(rule["from"]), Path(rule["to"])
                # Check if glob
                src_files = list(filter(os.path.isfile, glob.glob(src_path.as_posix(), recursive=True)))
                dst_files = []
                if src_files:  # Glob found => copy all files matched directly to destination
                    dst_files.extend(
                        [
                            dst_path.joinpath(os.path.basename(f))
                            for f in strip_leading_dots(src_files)
                        ]
                    )
                elif src_path.exists():  # Not a glob pattern -> copy entire subdirs
                    if src_path.is_dir():
                        src_files = glob.glob(src_path.as_posix() + "/**", recursive=True)
                        src_files = list(filter(os.path.isfile, src_files))
                    else:
                        src_files = [src_path.as_posix()]

                    dst_files.extend(map(dst_path.joinpath, strip_leading_dots(src_files)))

                if CLEAN_ARG:
                    for s, d in zip(src_files, dst_files):
                        if d.exists():
                            os.remove(d)
                else:
                    for s, d in zip(src_files, dst_files):  # Create
                        d.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(s, d)

            # Run scripts
            if CLEAN_ARG:
                os.chdir(cwd)
                continue

            scripts = setup_file_data["scripts"]
            for script in scripts:
                runpy.run_path(script)

            # Change cwd back to original
            os.chdir(cwd)
