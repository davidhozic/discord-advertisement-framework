from contextlib import suppress
import inspect
import os
import sys
import re


# Set current working directory to scripts folder
for path, dirs, files in os.walk("./"):
    for dir in dirs:
        if dir == "scripts":
            os.chdir(os.path.join(path, dir))
            break


EXCEPTION_TEMPLATE =\
"""
| {error_name}| {error_code}| {error_message}|
+----------------------------------------+------+----------------------------------------------------------------------------------------------------------------------------+"""


export_e = """\
+----------------------------------------+------+----------------------------------------------------------------------------------------------------------------------------+
|     Name                               | Num  | Description                                                                                                                |
+========================================+======+============================================================================================================================+"""
fdata = ""
with open("../../src/framework/exceptions.py", "r") as f:
    fdata += f.read()

excs = re.findall(r"\w+.+#:.+", fdata)

for exc in excs:
    name = re.search(r"[A-z]+", exc).group(0)
    value = re.search(r"[0-9]+", exc).group(0)    
    description = re.search(r"(?<=#:).+", exc).group(0).strip()
    export_e += EXCEPTION_TEMPLATE.format(error_name=name + "".join(' ' for i in range(39-len(name))), error_code=value + "".join(' ' for i in range(5-len(value))), error_message=description + "".join(' ' for i in range(123-len(description))))

export_e += ""


with open("__autodoc_export_exceptions.rst", "w") as f:
    f.write(export_e)


