#!/bin/bash

python3 -m pip install virtualenv
python3 -m virtualenv .venv
. ./.venv/bin/activate
python3 -m pip install --editable .[all]
python3 -m pip install --editable .[docs]
python3 -m pip install --editable .[testing]

sudo apt-get update
sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-lang-european latexmk inkscape ffmpeg build-essential
