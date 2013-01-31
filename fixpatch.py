#!/usr/bin/python
# vim: sw=4 ts=4 et si:
"""
Take an existing patch and add the appropriate tags, drawing from known
repositories to discover the origin. Also, renames the patch using the
subject found in the patch itself.
"""

__revision__ = 'Revision: 2.0'
__author__ = 'Jeff Mahoney'


from patch import PatchException
from patch.Patch import PatchOps, Patch
from optparse import OptionParser
import sys
import os

def process_file(file, options):
    try:
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
            if options.reference:
                print >>sys.stderr, \
                      "References won't be updated in header-only mode."
                options.reference = None

        if not options.no_diffstat:
            p.add_diffstat()
        if not options.no_ack:
            p.add_signature(options.signed_off_by)

        if options.reference:
            p.add_references(options.reference)

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
    except PatchException, e:
        print >>sys.stderr, e

if __name__ == "__main__":
    parser = OptionParser(version='%prog ' + __revision__)
    parser.add_option("-n", "--dry-run", action="store_true", default=False,
                      help="Output results to stdout but don't commit change")
    parser.add_option("-N", "--no-ack", action="store_true", default=False,
                      help="Don't add Acked-by tag (will add by default)")
    parser.add_option("-D", "--no-diffstat", action="store_true", default=False,
                      help="Don't add the diffstat to the patch")
    parser.add_option("-r", "--no-rename", action="store_true", default=False,
                      help="Don't rename the patch")
    parser.add_option("-f", "--force", action="store_true", default=False,
                      help="Overwrite patch if it exists already")
    parser.add_option("-H", "--header-only", action="store_true", default=False,
                      help="Only update the patch headers, don't do Acked-by or Diffstat")
    parser.add_option("-U", "--update-only", action="store_true", default=False,
                      help="Update the patch headers but don't rename (-Hr)")
    parser.add_option("-R", "--name-only", action="store_true", default=False,
                      help="Print the new filename for the patch but don't change anything")
    parser.add_option("-F", "--reference", action="append", default=None,
                      help="add reference tag")
    parser.add_option("-S", "--signed-off-by", action="store_true",
		      default=False,
		      help="Use Signed-off-by instead of Acked-by")

    (options, args) = parser.parse_args()

    if not args:
        parser.error("Must supply patch filename(s)")
        sys.exit(1)

    for file in args:
        process_file(file, options)

    sys.exit(0)
