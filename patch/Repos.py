#!/usr/bin/env python
"""
Represent Git Repos
"""

import os
from ConfigParser import ConfigParser


class Repos:
    def __init__(self):
        config = ConfigParser()
        config.read(['/etc/patch.cfg', os.path.expanduser('~/.patch.cfg'), './patch.cfg'])
        self.repos = config.get('patch', 'repos').split()
        self.mainline_repos = config.get('patch', 'mainline_repos').split()

    def _canonicalize(self, path):
        if path[0] == '/':
            return os.path.realpath(path)
        elif path == ".":
            return os.getcwd()
        else:
            return path

    def get_repos(self):
        return list(self._canonicalize(r) for r in self.repos)

    def get_mainline_repos(self):
        return list(self._canonicalize(r) for r in self.mainline_repos)

    def get_default_mainline_repo(self):
        return self._canonicalize(self.mainline_repos[0])



