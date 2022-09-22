import os
import setuptools
import json



long_description = None
with open("./README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

req = None
with open("./requirements.txt" , 'r', encoding="utf-8") as rf:
    req = rf.readlines()

version = ""
with open("./version.txt", "r", encoding="utf-8") as rf:
    version = rf.read().strip()

optional_install = None
with open("./optional.json", "r", encoding="utf-8") as rf:
    optional_install = json.load(rf)



__metadata__ = \
{
    "version" : version,
    "requirements" : req,
    "minimum_py_version" : "3.8",
}


setuptools.setup(
    name="Discord-Advert-Framework",
    version=__metadata__["version"],
    author="David Hozic",
    author_email="davidhozic@gmail.com",
    description="Framework (or bot) that allows you to advertise on discord",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://daf.davidhozic.top/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=f">={__metadata__['minimum_py_version']}",
    install_requires=__metadata__["requirements"],
    include_package_data=True,
    extras_require=optional_install
)
