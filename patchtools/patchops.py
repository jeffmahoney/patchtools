# vim: sw=4 ts=4 et si:
"""
Support package for doing SUSE Patch operations
"""

from patchtools import PatchException
from subprocess import Popen, PIPE
import re

def key_version(tag):
    m = re.match("v2\.(\d+)\.(\d+)(\.(\d+)|-rc(\d+)|)", tag)
    if m:
        major = 2
        minor = int(m.group(1))
        patch = int(m.group(2))
        if m.group(5):
            return (major, minor, patch, False, m.group(5))
        else:
            mgroup4=m.group(4) if m.group(4) else ""
            return (major, minor, patch, True, mgroup4)

    m = re.match("v(\d+)\.(\d+)(\.(\d+)|-rc(\d+)|)", tag)
    if m:
        major = int(m.group(1))
        minor = int(m.group(2))
        patch = 0
        if m.group(5):
            return (major, minor, patch, False, m.group(5))
        else:
            if m.group(4):
                    patch = int(m.group(4))
            return (major, minor, patch, True, "")

    return ""

class LocalCommitException(PatchException):
    pass

class PatchOps:
    @staticmethod
    def get_tag(commit, repo):
        command = "(cd %s;git name-rev --refs=refs/tags/v* %s)" % (repo, commit)

        cmd = Popen(command, shell=True, text=True,
                    stdout=PIPE, stderr=open("/dev/null", "w"))
        tag = cmd.communicate()[0]

        if tag == "":
            return None

        m = re.search("tags/([a-zA-Z0-9\.-]+)\~?\S*$", tag)
        if m:
            return m.group(1)
        m = re.search("(undefined)", tag)
        if m:
            return m.group(1)
        return None

    @staticmethod
    def get_next_tag(repo):
        command = "(cd %s ; git tag -l 'v*')" % repo
        cmd = Popen(command, shell=True, text=True,
                    stdout=PIPE, stderr=open("/dev/null", "w"))
        tag = cmd.communicate()[0]

        if tag == "":
            return None

        lines = tag.split()
        lines.sort(key=key_version)
        lasttag = lines[len(lines) - 1]

        m = re.search("v([0-9]+)\.([0-9]+)(|-rc([0-9]+))$", lasttag)
        if m:
            # Post-release commit with no rc, it'll be rc1
            if m.group(3) == "":
                nexttag = "v%s.%d-rc1" % (m.group(1), int(m.group(2)) + 1)
            else:
                nexttag = "v%s.%d or v%s.%s-rc%d (next release)" % \
                          (m.group(1), int(m.group(2)), m.group(1),
                           m.group(2), int(m.group(4)) + 1)
            return nexttag

        return None

    @staticmethod
    def get_diffstat(message):

        cmd = Popen("diffstat -p1", shell=True, text=True,
                    stdin=PIPE, stdout=PIPE)

        out = cmd.communicate(message)[0]

        return out

    @staticmethod
    def get_git_repo_url(dir):
        command = "(cd %s; git remote show origin -n)" % dir
        cmd = Popen(command, shell=True, text=True,
                    stdout=PIPE, stderr=open("/dev/null", "w"))
        for line in cmd.communicate()[0].split('\n'):
            m = re.search("URL:\s+(\S+)", line)
            if m:
                return m.group(1)

        return None

    @staticmethod
    def confirm_commit(commit, repo):
        cmd = Popen("cd %s ; git rev-list HEAD --not --remotes $(git config --get branch.$(git symbolic-ref --short HEAD).remote)" % repo,
                    shell=True, text=True,
                    stdout=PIPE, stderr=open("/dev/null", "w"))
        out = cmd.communicate()[0]
        if out == "":
            return True

        commits = out.split()
        if commit in commits:
            return False
        return True

    @staticmethod
    def get_commit(commit, repo, force=False):
        cmd = Popen("cd %s ; git diff-tree --no-renames --pretty=email -r -p --cc --stat %s" % \
                    (repo, commit),
                    shell=True, text=True,
                    stdout=PIPE, stderr=open("/dev/null", "w"))
        data = cmd.communicate()[0]
        if data == "":
            return None

        if not force and not PatchOps.confirm_commit(commit, repo):
            raise LocalCommitException("Commit is not in the remote repository. Use -f to override.")

        return data

    @staticmethod
    def safe_filename(name):
        if name is None:
            return name
        name = re.sub('\[PATCH[^]]*\]', '', name)
        name = re.sub('\[.*[^]]*\]', '', name)
        name = re.sub('^ *', '', name)
        name = re.sub('[\[\]\(\)]', '', name)
        name = re.sub('\|', '_', name)
        name = re.sub('[^_A-Z0-9a-z/ ]', '-', name)
        name = re.sub('[ /]', '-', name)
        name = re.sub('--*', '-', name)
        name = re.sub('-_', '-', name)
        name = re.sub('-$', '', name)
        name = re.sub('^-*', '', name)
        name = re.sub('^staging-', '', name)

        return name.lower()
