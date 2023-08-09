# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     ?= source
BUILDDIR      ?= build
USE_LANGUAGE  ?= sl

export LANGUAGE=$(USE_LANGUAGE)

_BUILD_DIR = $(BUILDDIR)/$(SOURCEDIR)

# OS specific commands
ifeq ($(OS), Windows_NT)
LATEX_CMD := \
	cp $(CURDIR)/build-latex-win.sh $(CURDIR)/$(_BUILD_DIR)/latex/ &&\
	wsl --cd $(CURDIR)/$(_BUILD_DIR)/latex sh build-latex-win.sh

else
LATEX_CMD := cd $(CURDIR)/$(_BUILD_DIR)/latex && make all-pdf
endif


# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).

clean:
	python3 ./setup.py --clean --start-dir $(SOURCEDIR)
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(_BUILD_DIR)" $(SPHINXOPTS) $(O)

pdf: latex
	mkdir -p $(CURDIR)/$(_BUILD_DIR)/pdf/
	$(LATEX_CMD)
	cp $(CURDIR)/$(_BUILD_DIR)/latex/*.pdf $(CURDIR)/$(_BUILD_DIR)/pdf/

%: Makefile
	python3 ./setup.py --start-dir $(SOURCEDIR)
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(_BUILD_DIR)" $(SPHINXOPTS) $(O)
