# vim: sw=4 ts=4 et si:
"""
Support package for doing SUSE Patch operations
"""

from patchtools import PatchException
from patchtools.command import run_command
import re

def key_version(tag):
    m = re.match("v2\.(\d+)\.(\d+)(\.(\d+)|-rc(\d+)|)", tag)
    if m:
        major = 2
        minor = int(m.group(1))
        patch = int(m.group(2))
        if m.group(5):
            return (major, minor, patch, False, int(m.group(5)))
        else:
            mgroup4=int(m.group(4)) if m.group(4) else 0
            return (major, minor, patch, True, mgroup4)

    # We purposely ignore x.y.z tags since those are from -stable and
    # will never be used in a mainline tag.
    m = re.match("v(\d+)\.(\d+)(-rc(\d+)|)", tag)
    if m:
        major = int(m.group(1))
        minor = int(m.group(2))
        if m.group(4):
                return (major, minor, 0, False, int(m.group(4)))
        return (major, minor, 0, True, "")

    return ()

class LocalCommitException(PatchException):
    pass

def get_tag(commit, repo):
    command = f"(cd {repo};git name-rev --refs=refs/tags/v* {commit})"
    tag = run_command(command)
    if tag == "":
        return None

    m = re.search("tags/([a-zA-Z0-9\.-]+)\~?\S*$", tag)
    if m:
        return m.group(1)
    m = re.search("(undefined)", tag)
    if m:
        return m.group(1)
    return None

def get_next_tag(repo):
    command = f"(cd {repo} ; git tag -l 'v[0-9]*')"
    tag = run_command(command)
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

def get_diffstat(message):
    return run_command("diffstat -p1", input=message)

def get_git_repo_url(dir):
    command = f"(cd {dir}; git remote show origin -n)"
    output = run_command(command)
    for line in output.split('\n'):
        m = re.search("URL:\s+(\S+)", line)
        if m:
            return m.group(1)

    return None

def confirm_commit(commit, repo):
    command = f"cd {repo} ; git rev-list HEAD --not --remotes $(git config --get branch.$(git symbolic-ref --short HEAD).remote)"
    out = run_command(command)
    if out == "":
        return True

    commits = out.split()
    if commit in commits:
        return False
    return True

def canonicalize_commit(commit, repo):
    return run_command(f"cd {repo} ; git show -s {commit}^{{}} --pretty=%H")

def get_commit(commit, repo, force=False):
    command = f"cd {repo}; git diff-tree --no-renames --pretty=email -r -p --cc --stat {commit}"
    data = run_command(command)
    if data == "":
        return None

    if not force and not confirm_commit(commit, repo):
        raise LocalCommitException("Commit is not in the remote repository. Use -f to override.")

    return data

def safe_filename(name, keep_non_patch_brackets = True):
    if name is None:
        return name

    # These mimic the filters that git-am applies when it parses the email
    # to remove noise from the subject line.
    # keep_non_patch_brackets=True is the equivalent of git am -b
    if keep_non_patch_brackets:
        name = re.sub('(([Rr][Ee]:|\[PATCH[^]]*\])[ \t]*)*', '', name, 1)
    else:
        name = re.sub('(([Rr][Ee]:|\[[^]]*\])[ \t]*)*', '', name, 1)

    # This mimics the filters that git-format-patch applies prior to adding
    # prefixes or suffixes.
    name = re.sub('[^_A-Z0-9a-z\.]', '-', name)
    name = re.sub('-+', '-', name)
    name = re.sub('\.+', '.', name)
    return name.strip('-. ')
