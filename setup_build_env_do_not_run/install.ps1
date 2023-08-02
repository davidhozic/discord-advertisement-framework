# Installs required build packages
echo "Creating Python  environment"
python3 -m pip install virtualenv
python3 -m virtualenv .venv
.\.venv\Scripts\activate
cp .\.venv\Scripts\python.exe .\.venv\Scripts\python3.exe
cp .\.venv\Scripts\pythonw.exe .\.venv\Scripts\python3w.exe
python3 -m pip install --editable .[all]
python3 -m pip install --editable .[docs]
python3 -m pip install --editable .[testing]

# Intall scoop package manager and packages
echo "Installing packages"
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex
scoop bucket add extras
scoop install ffmpeg-shared inkscape

# Install TexLive inside WSL
wsl sudo apt install -y texlive-latex-base texlive-latex-extra texlive-lang-european latexmk build-essential
