import setuptools, json




with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

metadata = \
{
    "name"                  : "DS-Framework",
    "author"                : "David Hozic",
    "version"               : "v1.6.1",
    "author_email"          : "davidhozic@gmail.com",
    "description"           : "Shilling framework that allows periodic self promotion on discord, can be used for shilling NFTs or anything else",
    "github_url"            : "https://github.com/davidhozic/Discord-Shilling-Framework",
    "required_py_version"   : ">=3.6"
}





####################################################################################################
setuptools.setup(
    name=metadata["name"],
    version=metadata["version"],
    author=metadata["author"],
    author_email=metadata["author_email"],
    description=metadata["description"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=metadata["github_url"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "framework"},
    packages=setuptools.find_packages(where="framework"),
    python_requires=metadata["required_py_version"],
)