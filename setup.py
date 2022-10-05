import os
import setuptools
import json



long_description = None
with open("./README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

req = None
with open("./requirements.txt" , 'r', encoding="utf-8") as rf:
    req = rf.readlines()

optional_install = None
with open("./optional.json", "r", encoding="utf-8") as rf:
    optional_install: dict = json.load(rf)
    # Make a key that will install all requirements
    all_deps = []
    for key, deps in optional_install.items():
        if key == "docs":
            continue
        
        all_deps.extend(deps)
    
    optional_install["all"] = all_deps

# Parse version
gh_release = os.environ.get("GITHUB_REF_NAME", default=None) # Workflow run release
readthedocs_release = os.environ.get("READTHEDOCS_VERSION", default=None) # Readthe docs version

version = None
if gh_release is not None:
    version = gh_release
elif readthedocs_release is not None:
    version = readthedocs_release
else:
    with open("./version.txt", "r", encoding="utf-8") as rf:
        version = rf.read().strip()


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
