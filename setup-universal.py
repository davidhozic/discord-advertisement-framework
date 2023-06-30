"""
Script removes a line inside pyproject.toml forcing a normal wheel to be created.
"""
import re

with open("./pyproject.toml", "r") as reader:
    data = re.sub("build-backend.*", "", reader.read())

with open("./pyproject.toml", "w") as writer:
    writer.write(data)
