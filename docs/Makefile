# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     ?= source
BUILDDIR      ?= build
USE_LANGUAGE  ?= en

export LANGUAGE=$(USE_LANGUAGE)

_BUILD_DIR = $(BUILDDIR)/$(SOURCEDIR)


# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).

clean:
	python3 ./setup.py --clean
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

pdf: latex
	docker run --rm -v $(CURDIR)/$(_BUILD_DIR)/latex:/home/ -w /home/ texlive/texlive make all-pdf
	mkdir -p $(CURDIR)/$(_BUILD_DIR)/pdf/
	cp $(CURDIR)/$(_BUILD_DIR)/latex/*.pdf $(CURDIR)/$(_BUILD_DIR)/pdf/


%: Makefile
	python3 ./setup.py
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(_BUILD_DIR)" $(SPHINXOPTS) $(O)
