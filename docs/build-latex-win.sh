# Script is created to speed up the latex compilation on the windows system though wsl.
# It copis all latex files to a wsl directory, runs the latex compiler and then copies them back
# to the orignal path.

ORIGIN_DIR=$(pwd)
LATEX_BUILD_PATH=~/latex-build/

# Copy the current folder (latex build folder) contents to our home folder
echo Creating dir $LATEX_BUILD_PATH
mkdir -p $LATEX_BUILD_PATH

echo Copying files to $LATEX_BUILD_PATH
cp -r $ORIGIN_DIR/** $LATEX_BUILD_PATH

echo Building latex
cd $LATEX_BUILD_PATH
make all-pdf
cp -r $LATEX_BUILD_PATH/** $ORIGIN_DIR

echo Cleaning up $LATEX_BUILD_PATH
rm -rf $LATEX_BUILD_PATH
