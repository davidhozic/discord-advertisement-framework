# Installs required build packages
echo "Creating Python  environment"
python3 -m pip install virtualenv
python3 -m virtualenv venv
.\venv\Scripts\activate
cp .\venv\Scripts\python.exe .\venv\Scripts\python3.exe
python3 -m pip install --editable .[all]
python3 -m pip install --editable .[docs]
python3 -m pip install --editable .[testing]

echo "Installing packages"
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex
scoop bucket add extras
scoop install mingw ffmpeg inkscape

$ProgressPreference = 'SilentlyContinue' # Way faster for some reason
echo "Downloading Docker"
Invoke-WebRequest -Uri https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe -OutFile 'Docker Desktop Installer.exe'

echo "Installing docker (for texlive)"
Start-Process 'Docker Desktop Installer.exe' -Wait install
