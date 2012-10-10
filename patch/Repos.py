#!/usr/bin/env python
"""
Support package for doing SUSE Patch operations
"""

import os


# everyplace to search for the commit it, in order of preference
repos = [
    ".",
    "/alt/linux/linux-2.6",
    "/alt/linux/scsi",
    "/alt/public_projects/tgt",
]

# everything that is the canonical mainline repos, so e.g. it has the
# local path and the canonical git location
mainline_repos = [
    "/alt/linux/linux-2.6",
    "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux-2.6.git",
    "/alt/linux/scsi",
    "git://git.kernel.org/pub/scm/linux/kernel/git/jejb/scsi.git",
]

#
# canonicalize pathnames
#

for index in range(0, len(mainline_repos)):
    if mainline_repos[index][0] == '/':
        mainline_repos[index] = os.path.realpath(mainline_repos[index])
    elif mainline_repos[index] == ".":
        mainline_repos[index] = os.getcwd()

for index in range(0, len(repos)):
    if repos[index][0] == '/':
        repos[index] = os.path.realpath(repos[index])
    elif repos[index] == ".":
        repos[index] = os.getcwd()





