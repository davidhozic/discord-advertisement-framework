"""
Scripts for generating thesis literature.
(As footnotes)
"""
from typing import List, Dict
import os
import json


OUTPUT_FILE = "../thesis_lit.rst"
SOURCES_FILE = "../sources.json"


# Setup
## All paths relative to script file location
os.chdir(os.path.dirname(__file__))

OUTPUT_HEADER = \
"""
..
      AUTOMATICALLY GENERATED 
    !!!!!!!!!!!!!!!!!!!!!!!!!!!
    !       DO NOT EDIT       !

===============
Sources
===============
"""
OUTPUT_FOOTER = "\n"

OUTPUT_FORMAT = \
"""
[{ind}]

    | Title: {title}
    | Author: {author}
    | Source: {source}
    | Last checked: {updated}
"""


# Main script
source_data = None
source_output = OUTPUT_HEADER

with open(SOURCES_FILE, "r", encoding="utf-8") as reader:
    source_data: List[Dict[str, str]] = json.load(reader)

for i, item in enumerate(source_data, 1):
    author=item["author"]
    title=item["title"].replace(":", r"\:")
    source=item["source"]
    updated=item["updated"]

    source_output += OUTPUT_FORMAT.format(
        ind=i,
        author=author,
        title=title,
        source=source,
        updated=updated,
    )

source_output += OUTPUT_FOOTER
with open(OUTPUT_FILE, "w", encoding="utf-8") as writer:
    writer.write(source_output)

