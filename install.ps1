# Installs required build packages

python3 -m pip install virtualenv
python3 -m virtualenv venv
.\venv\Scripts\activate
cp .\venv\Scripts\python.exe .\venv\Scripts\python3.exe
python3 -m pip install --editable .[all]
python3 -m pip install --editable .[docs]
python3 -m pip install --editable .[testing]

Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
choco install inkscape -y
choco install mingw -y
choco install docker-desktop -y

echo "Start Docker Desktop and run 'docker volume create miktex'"

