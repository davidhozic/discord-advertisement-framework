"
Installs required build packages
"

Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

choco install miktex -y
choco install inkscape -y
choco install mingw -y
