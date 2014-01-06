#!/usr/bin/env python
# vim: sw=4 ts=4 et si:
"""
Represent Git Repos
"""

import os
import site
from ConfigParser import ConfigParser, NoOptionError
from subprocess import Popen, PIPE
import re

MAINLINE_URLS = [ """git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux-2.6.git""", """git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git""" ]

def get_git_repo_url(dir):
    command = "(cd %s; git remote show origin -n)" % dir
    cmd = Popen(command, shell=True, stdout=PIPE,
                stderr=open("/dev/null", "w"))
    for line in cmd.communicate()[0].split('\n'):
        m = re.search("URL:\s+(\S+)", line)
        if m:
            return m.group(1)

    return None

# We deliberately don't catch exceptions when the option is mandatory
class Config:
    def __init__(self):
        config = ConfigParser()
        config.read([ '/etc/patch.cfg', 
                      '%s/etc/patch.cfg' % site.USER_BASE,
                       os.path.expanduser('~/.patch.cfg'),
                     './patch.cfg'])
        self.repos = config.get('repositories', 'search').split()
        self.mainline_repos = MAINLINE_URLS
        try:
            repos = config.get('repositories', 'mainline').split()
            self.mainline_repos += repos
        except NoOptionError, e:
            pass

        for repo in self.repos:
            url = get_git_repo_url(repo)
            if url in self.mainline_repos:
                self.mainline_repos += repo

        self.name = config.get('contact', 'name')
        self.emails = config.get('contact', 'email').split()
        self.email = self.emails[0]

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
