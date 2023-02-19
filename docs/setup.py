"""
Script that setups the environment before build.

Input
-----------
--setup-file
    The file that contains information about what to copy where
--scripts-to-run
    The scripts to run.
"""
from pathlib import Path

import subprocess
import re
import os
import glob
import shutil
import json
import sys

CLEAN = "--clean" in sys.argv

# Work relatively to the setup script location
os.chdir(os.path.dirname(__file__))

for path, dirs, files in os.walk("./"):
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
                    _dest = [os.path.join(cp_to, m.lstrip("./").lstrip("../")) for m in _src]
                else:
                    _src = [cp_from]
                    _dest = [cp_to]

                srcdest = zip(_src, _dest)
                for fromf, tof in srcdest:
                    if CLEAN:
                        if os.path.exists(tof):
                            os.remove(tof)
                    else:
                        tof_dir = Path(os.path.dirname(tof))
                        tof_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(fromf, tof)

            # Run scripts
            scripts = setup_file_data["scripts"]
            for script in scripts:
                process = subprocess.Popen([sys.executable, script], universal_newlines=True)
                process.communicate()

            # Change cwd back to original
            os.chdir(cwd)

