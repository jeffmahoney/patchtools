#!/usr/bin/python3
# vim: sw=4 ts=4 et si:
"""
Setup file for installation
"""

import os
import sys
import shutil
import site
from distutils.core import setup, Command

setup(
    author="Jeff Mahoney",
    author_email="jeffm@suse.com",
    name="patchtools",
    packages=["patchtools"],
    scripts=["scripts/exportpatch", "scripts/fixpatch"],
    version="2.4")
