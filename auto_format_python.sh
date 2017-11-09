#!/usr/bin/env bash

#
# Runs yapf on all python files here. See https://github.com/google/yapf
#
# See statistics:
# pep8 --statistics --filename *.py
#

yapf --in-place *.py addons/*/*.py
