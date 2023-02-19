#!/bin/bash

python3 -m pip install virtualenv
python3 -m virtualenv venv
. ./venv/bin/activate
python3 -m pip install --editable .[all]
python3 -m pip install --editable .[docs]
python3 -m pip install --editable .[testing]

sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin inkscape ffmpeg

sudo groupadd docker
sudo gpasswd -a $USER docker
sudo service docker start
