#!/usr/bin/python
"""
Fix a patch?
"""

__revision__ = 'Revision: 2.0'
__author__ = 'Jeff Mahoney'


from patch.Patch import PatchOps, Patch
from optparse import OptionParser
import sys
import os


def get_filename(p, dir=None):
    if p.message and p.message['Subject']:
        fn = PatchOps.safe_filename(p.message['Subject'])
        if dir:
            fn = dir + os.sep + fn
        return fn
    else:
        raise Exception("No subject line")

def process_file(file, options):
    p = Patch()
    f = open(file, "r")
    p.from_email(f.read())

    if options.name_only:
        fn = p.get_pathname()
        print fn
        return

    if options.update_only:
        options.header_only = True
        options.no_rename = True

    if options.header_only:
        options.no_ack = True
        options.no_diffstat = True

    if not options.no_diffstat:
        p.add_diffstat()
    if not options.no_ack:
        p.add_acked_by()

    if options.dry_run:
        print p.message.as_string(unixfrom=False)
        return

    if options.no_rename:
        fn = file
    else:
        fn = p.get_pathname()
        if fn != file and os.path.exists(fn) and not options.force:
            print >> sys.stderr, "%s already exists." % fn
            return
    print fn
    f = open(fn, "w")
    print >> f, p.message.as_string(unixfrom=False)
    f.close()
    if fn != file:
        os.unlink(file)

if __name__ == "__main__":
    parser = OptionParser(version='%prog ' + __revision__)
    parser.add_option("-n", "--dry-run", action="store_true", default=False)
    parser.add_option("-N", "--no-ack", action="store_true", default=False)
    parser.add_option("-D", "--no-diffstat", action="store_true", default=False)
    parser.add_option("-r", "--no-rename", action="store_true", default=False)
    parser.add_option("-f", "--force", action="store_true", default=False)
    parser.add_option("-H", "--header-only", action="store_true", default=False)
    parser.add_option("-U", "--update-only", action="store_true", default=False)
    parser.add_option("-R", "--name-only", action="store_true", default=False)

    (options, args) = parser.parse_args()

    if not args:
	parser.error("Must supply patch filename(s)")
	sys.exit(1)

    for file in args:
        process_file(file, options)

    sys.exit(0)
