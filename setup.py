import setuptools




with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


__metadata__ = \
{
    "version" :  "1.7.1",
    "requirements" :  ["aiohttp>=3.6.0,<3.9.0"],
    "minimum_py_version" :  "3.8",
}

setuptools.setup(
    name="Discord-Shilling-Framework",
    version=__metadata__["version"],
    author="David Hozic",
    author_email="davidhozic@gmail.com",
    description="Discord Shilling/Self-Promo Framework for shilling, eg. NFT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/davidhozic/Discord-Shilling-Framework",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=f">={__metadata__['minimum_py_version']}",
    install_requires=__metadata__["requirements"]
)