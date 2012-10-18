#!/usr/bin/env python
# vim: sw=4 ts=4 et si:
"""
Export a patch from a repository with the SUSE set of patch headers.
From Jeff Mahoney, updated by Lee Duncan.
"""

__revision__ = 'Revision: 2.0'
__author__ = 'Jeff Mahoney'

import sys
import re
from patch.Patch import Patch, PatchException
from optparse import OptionParser
from urlparse import urlparse
import os


# default: do not write out a patch file
WRITE=False

# default directory where patch gets written
DIR="."

def export_patch(commit, options):
    try:
        p = Patch(commit, debug=options.debug, force=options.force)
    except PatchException, e:
        print >>sys.stderr, e
        return None
    if p.find_commit():
        if options.reference:
            p.add_references(options.reference)
        if options.extract:
            p.filter(options.extract)
        p.add_acked_by()
        if options.write:
            fn = p.get_pathname(options.dir)
            if os.path.exists(fn) and not options.force:
                f = fn
                fn += "-%s" % commit[0:8]
                print >>sys.stderr, "%s already exists. Using %s" % (f, fn)
            print os.path.basename(fn)
            try:
                f = open(fn, "w")
            except Exception, e:
                print >>sys.stderr, "Failed to write %s: %s" % (fn, e)
                raise e

            print >>f, p.message
            f.close()
        else:
            print p.message
    else:
        print >>sys.stderr, "Couldn't locate commit \"%s\"; Skipping." % commit

if __name__ == "__main__":
    parser = OptionParser(version='%prog ' + __revision__,
                          usage='%prog [options] <LIST OF COMMIT HASHES> --  export patch with proper patch headers')
    parser.add_option("-w", "--write", action="store_true",
                      help="write patch file(s) instead of stdout [default is %default]",
                      default=WRITE)
    parser.add_option("-d", "--dir", action="store",
                      help="write patch to this directory (default '.')", default=DIR)
    parser.add_option("-f", "--force", action="store_true",
                      help="write over existing patch or export commit that only exists in local repo", default=False)
    parser.add_option("-D", "--debug", action="store_true",
                      help="set debug mode", default=False)
    parser.add_option("-F", "--reference", action="append",
                      help="add reference tag. This option can be specified multiple times.", default=None)
    parser.add_option("-x", "--extract", action="append",
                      help="extract specific parts of the commit; using a path that ends with / includes all files under that hierarchy. This option can be specified multiple times.", default=None)
    (options, args) = parser.parse_args()

    if not args:
        parser.error("Must supply patch hash(es)")
        sys.exit(1)

    for commit in args:
        export_patch(commit, options)

    sys.exit(0)
