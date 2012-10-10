#
"""patch class"""

import os

__version__ = '1.1'

__all__ = [
	"Patch",
	"PatchOps",
]

# everyplace to search for the commit it, in order of preference
repos = [
    ".",
    "/alt/linux/linux-upstream",
    "/alt/linux/scsi-misc-2.6"
]

# everything that is the canonical mainline repos, so e.g. it has the
# local path and the canonical git location
mainline_repos = [
    "/alt/linux/linux-upstream",
    "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux-2.6.git",
]

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

