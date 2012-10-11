#!/usr/bin/env python
"""
Setup file for installation
"""

import os
import sys
import shutil
from distutils.core import setup, Command


class CleanCommand(Command):
    description = "custom clean command that forcefully removes dist/build directories"
    user_options = []
    def initialize_options(self):
        self.cwd = None
    def finalize_options(self):
        self.cwd = os.getcwd()
    def run(self):
        assert os.getcwd() == self.cwd, 'Must be in package root: %s' % self.cwd
        print "removing './build', and everything under it"
        os.system('rm -rf ./build')
        print "removing './scripts', and everything under it"
        os.system('rm -rf ./scripts')

shutil.rmtree("scripts", ignore_errors=True)
os.makedirs("scripts")
shutil.copyfile("exportpatch.py", "scripts/exportpatch")
shutil.copyfile("fixpatch.py", "scripts/fixpatch")

setup(# distribution meta-data
        cmdclass={
            'clean': CleanCommand
            },
        author="Lee Duncan",
        author_email="lee@gonzoleeman.net",
        name="patchopts",
        packages=["patch"],
        scripts=["scripts/exportpatch", "scripts/fixpatch"],
        version="2.0",
	data_files=[('/etc', ['patch.cfg'])])
