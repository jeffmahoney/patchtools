#!/usr/bin/env python
# vim: sw=4 ts=4 et si:
"""
Represent Git Repos
"""

import os
from ConfigParser import ConfigParser, NoOptionError

MAINLINE_URL = """git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux-2.6.git"""

class Repos:
    def __init__(self):
        config = ConfigParser()
        config.read(['/etc/patch.cfg', os.path.expanduser('~/.patch.cfg'),
                     './patch.cfg'])
        self.repos = config.get('repositories', 'search').split()
        self.mainline_repos = [ MAINLINE_URL ]
        try:
            repos = config.get('repositories', 'mainline').split()
            self.mainline_repos += repos
        except NoOptionError, e:
            pass

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
