"""
Scripts for generating thesis literature.
(As footnotes)
"""
from typing import List, Dict
import os
import json


OUTPUT_FILE = "../source/thesis/thesis_lit.rst"
SOURCES_FILE = "../source/thesis/sources.json"


# Setup
## All paths relative to script file location
os.chdir(os.path.dirname(__file__))
## Format
OUTPUT_HEADER = \
"=======================\n"\
"Literature\n"\
"=======================\n"

OUTPUT_FORMAT = \
"""
.. _`{title}`:

[{ind}] {author}, "{title}" - {source} [Last checked: {updated}]
"""
TITLE_REPLACEMENT_CHARS = {' ', ',', ".", "!", "-"}


# Main script
source_data = None
source_output = OUTPUT_HEADER
with open(SOURCES_FILE, "r", encoding="utf-8") as reader:
    source_data: List[Dict[str, str]] = json.load(reader)

for i, item in enumerate(source_data):
    source_output += OUTPUT_FORMAT.format(
        ind=i,
        author=item["author"],
        title=item["title"],
        source=item["source"],
        updated=item["updated"]
    )


with open(OUTPUT_FILE, "w", encoding="utf-8") as writer:
    writer.write(source_output)

