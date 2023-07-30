"""
Script that setups the environment before build.
"""

from pathlib import Path
from argparse import ArgumentParser

import runpy
import re
import os
import glob
import shutil
import json


parse = ArgumentParser()
parse.add_argument("--clean", action="store_true", default=False, help="If given, it will only clean instead of copy and run")
parse.add_argument("--start-dir", default="./", dest="start_dir", help="Where to start looking for dep_local.json")
args = parse.parse_args()


CLEAN_ARG: bool = args.clean
START_DIR_ARG: str = args.start_dir

# Work relatively to the setup script location
os.chdir(os.path.dirname(__file__))

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
            # [(from, to), (from, to)]
            destinations = setup_file_data["copy"]
            for dest in destinations:
                cp_from = dest["from"]
                cp_to = dest["to"]
                if re.search(r"\.[A-z]+$", cp_to) is None:  # The path does not have extension -> assume a dir
                    _src = [x for x in glob.glob(cp_from, recursive=True) if os.path.isfile(x)]
                    _dest = [os.path.join(cp_to, os.path.basename(m)) for m in _src]
                else:
                    _src = [cp_from]
                    _dest = [cp_to]

                srcdest = zip(_src, _dest)
                for fromf, tof in srcdest:
                    if CLEAN_ARG:
                        if os.path.exists(tof):
                            os.remove(tof)
                    else:
                        tof_dir = Path(os.path.dirname(tof))
                        tof_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(fromf, tof)

            # Run scripts
            if CLEAN_ARG:
                os.chdir(cwd)
                continue

            scripts = setup_file_data["scripts"]
            for script in scripts:
                runpy.run_path(script)

            # Change cwd back to original
            os.chdir(cwd)
