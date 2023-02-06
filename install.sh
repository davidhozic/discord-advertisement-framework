#!bash

python3 -m pip install virtualenv
python3 -m virtualenv venv
. ./venv/bin/activate
python3 -m pip install --editable .[all]
python3 -m pip install --editable .[docs]
python3 -m pip install --editable .[testing]

apt-get update
apt-get install -y texlive texlive-science
apt-get install -y inkscape
