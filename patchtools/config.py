# vim: sw=4 ts=4 et si:
"""
Represent Git Repos
"""

import os
import pwd
import site
import configparser
from subprocess import Popen, PIPE
import re

MAINLINE_URLS = [ """git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux-2.6.git""", """git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git""" ]

def get_git_repo_url(gitdir):
    command = "(cd %s; git remote show origin -n)" % gitdir
    cmd = Popen(command, shell=True, text=True,
                stdout=PIPE, stderr=open("/dev/null", "w"))
    for line in cmd.communicate()[0].split('\n'):
        m = re.search("URL:\s+(\S+)", line)
        if m:
            return m.group(1)

    return None

def get_git_config(gitdir, var):
    command = "(cd {}; git config {})".format(gitdir, var)
    cmd = Popen(command, shell=True, text=True,
                stdout=PIPE, stderr=open("/dev/null", "w"))
    return cmd.communicate()[0].strip()

# We deliberately don't catch exceptions when the option is mandatory
class Config:
    def __init__(self):
        # Set some sane defaults
        self.repos = [ os.getcwd() ]
        self.mainline_repos = MAINLINE_URLS
        self.merge_mainline_repos()
        self.email = get_git_config(os.getcwd(), "user.email")
        self.emails = [self.email]
        self.name = pwd.getpwuid(os.getuid()).pw_gecos.split(",")[0].strip()

        self.read_configs()
        self.merge_mainline_repos()

    def read_configs(self):
        config = configparser.ConfigParser()
        files_read = config.read([ '/etc/patch.cfg',
                                   '%s/etc/patch.cfg' % site.USER_BASE,
                                   os.path.expanduser('~/.patch.cfg'),
                                   './patch.cfg'])
        try:
            self.repos = config.get('repositories', 'search').split()
            repos = config.get('repositories', 'mainline').split()
            self.mainline_repos += repos
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            pass

        try:
            self.name = config.get('contact', 'name')
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            pass

        try:
            self.emails = config.get('contact', 'email').split()
            self.email = self.emails[0]
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            pass

    def merge_mainline_repos(self):
        for repo in self.repos:
            url = get_git_repo_url(repo)
            if url in self.mainline_repos:
                self.mainline_repos += repo

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
