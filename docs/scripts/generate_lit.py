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


OUTPUT_FORMAT = \
"""
.. [{ind}] {author}, "{title}" - {source} [Last checked: {updated}]
"""


# Main script
source_data = None
source_output = ""
with open(SOURCES_FILE, "r", encoding="utf-8") as reader:
    source_data: List[Dict[str, str]] = json.load(reader)

for i, item in enumerate(source_data, 1):
    ind = str(i)
    if i % 10 == 1:
        ind += "st"
    elif i % 10 == 2:
        ind += "nd"
    elif i % 10 == 3:
        ind += "rd"
    else:
        ind += "th"
    
    source_output += OUTPUT_FORMAT.format(
        ind=ind,
        author=item["author"],
        title=item["title"],
        source=item["source"],
        updated=item["updated"]
    )


with open(OUTPUT_FILE, "w", encoding="utf-8") as writer:
    writer.write(source_output)

