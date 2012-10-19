#!/usr/bin/env python
# vim: sw=4 ts=4 et si:
"""
Support package for doing SUSE Patch operations
"""

from patch.PatchOps import PatchOps
from patch import config, PatchException
import re
import os
import email.parser
import urllib
from urlparse import urlparse
import string

_patch_start_re = re.compile("^(---|\*\*\*|Index:)[ \t][^ \t]|^diff -|^index [0-9a-f]{7}")

class InvalidCommitIDException(PatchException):
    pass

class InvalidPatchException(PatchException):
    pass

class InvalidURLException(PatchException):
    pass

class EmptyCommitException(PatchException):
    pass

class Patch:
    def __init__(self, commit=None, repo=None, debug=False, force=False):
        self.commit = commit
        self.repo = repo
        self.debug = debug
        self.force = force
        self.repourl = None
        self.message = None
        self.repo_list = config.get_repos()
        self.mainline_repo_list = config.get_mainline_repos()
        self.in_mainline = False
        if repo in self.mainline_repo_list:
            self.in_mainline = True
        if self.debug:
            print "DEBUG: repo_list:", self.repo_list

        if commit and (re.search("\^", commit) or re.search("HEAD", commit)):
            raise InvalidCommitIDException("Commit IDs must be hashes, not relative references. HEAD and ^ are not allowed.")

    def add_diffstat(self):
        for line in self.message.get_payload().splitlines():
            if re.search("[0-9]+ files? changed, [0-9]+ insertion", line):
                return

        diffstat = PatchOps.get_diffstat(self.body())
        text = ""
        switched = False
        need_sep = True
        body = ""

        for line in self.header().splitlines():
            if re.match("^---$", line) and not switched:
                need_sep = False

        if need_sep:
            diffstat = "---\n" + diffstat
        else:
            diffstat = "\n" + diffstat
        diffstat += "\n"

        header = self.header().rstrip() + "\n"
        self.message.set_payload(header + diffstat + self.body())

    def strip_diffstat(self):
        text = ""
        eat = ""
        for line in self.header().splitlines():
            if re.search("#? .* \| ", line):
                eat = eat + line + "\n"
                continue
            if re.match("#? .* files? changed(, .* insertions?\(\+\))?(, .* deletions?\(-\))?", line):
                eat = ""
                continue
            text += eat + line + "\n"
            eat = ""

        self.message.set_payload(text + "\n" + self.body())

    def update_diffstat(self):
        self.strip_diffstat()
        self.add_diffstat()

    def add_references(self, newrefs):
        if 'References' in self.message:
            refs = self.message['References'].split()
            for ref in refs:
                if ref in newrefs:
                    newrefs.remove(ref)

            refs += newrefs
            refs.sort()
            self.message.replace_header('References', string.join(refs, ' '))
        else:
            newrefs.sort()
            self.message.add_header('References', string.join(newrefs, ' '))

    def add_acked_by(self):
        for line in self.message.get_payload().splitlines():
            for email in config.emails:
                if re.search("Acked-by.*%s" % email, line) or \
                   re.search("Signed-off-by.*%s" % email, line):
                    return

        text = ""
        last = ""
        for line in self.message.get_payload().splitlines():
            if re.match("^---$", line):
                text = text.rstrip() + "\n"

                # If this is the first *-by tag, separate it
                if not re.search("-by: ", last):
                    text += "\n"
                text += "Acked-by: %s <%s>\n" % (config.name, config.email)
            text += line + "\n"
            last = line

        self.message.set_payload(text)

    def from_email(self, msg):
        p = email.parser.Parser()
        self.message = p.parsestr(msg)

        if 'Git-commit' in self.message:
            self.commit = self.message['Git-commit']

        if not self.repo:
            f = self.find_repo()
            env_from = self.message.get_unixfrom()
            if not f and env_from is not None:
                m = re.match("From (\S{40})", env_from)
                if m:
                    self.commit = m.group(1)
                    self.find_repo()

        if self.repo in self.mainline_repo_list:
            self.in_mainline = True
        elif self.repo and not self.message['Git-repo']:
            r = self.repourl
            if not r:
                    r = PatchOps.get_git_repo_url(self.repo)
            if r and r not in self.mainline_repo_list:
                self.message.add_header('Git-repo', r)
                self.repourl = r

        if self.commit and not self.message['Git-commit']:
            self.message.add_header('Git-commit', self.commit)

        if self.in_mainline:
            tag = PatchOps.get_tag(self.commit, self.repo)
            if tag and tag == "undefined":
                    tag = PatchOps.get_next_tag(self.repo)
            if tag:
                if 'Patch-mainline' in self.message:
                    self.message.replace_header('Patch-mainline', tag)
                else:
                    self.message.add_header('Patch-mainline', tag)
        elif self.message['Git-commit'] and self.repourl and \
              re.search("git.kernel.org", self.repourl):
            if 'Patch-mainline' in self.message:
                self.message.replace_header('Patch-mainline',
                                        "Queued in subsystem maintainer repo")
            else:
                self.message.add_header('Patch-mainline',
                                        "Queued in subsystem maintainer repo")
        self.handle_merge()

    def from_file(self, file):
        f = open(file, "r")
        self.from_email(f.read())
        f.close()

    def files(self):
        diffstat = PatchOps.get_diffstat(self.body())
        f = []
        for line in diffstat.splitlines():
            m = re.search("#? (\S+) \| ", line)
            if m:
                f.append(m.group(1))
            if not f:
                return None
            return f

    def find_commit(self):
        for repo in self.repo_list:
            commit = PatchOps.get_commit(self.commit, repo, self.force)
            if commit is not None:
                self.repo = repo
                self.from_email(commit)
                return True
        return False

    def parse_commitdiff_header(self):
        url = self.message['X-Git-Url']
        url = urllib.unquote(url)

        uc = urlparse(url)
        if not uc.scheme:
            raise InvalidURLException("X-Git-Url provided but is not a URL (%s)" % url)

        args = dict(map(lambda x : x.split('=', 1), uc.query.split(';')))
        if 'p' in args:
            args['p'] = urllib.unquote(args['p'])

        if uc.netloc == 'git.kernel.org':
            self.repo = None
            self.repourl = 'git://%s/pub/scm/%s' % (uc.netloc, args['p'])
        # Add more special cases here
        else:
            self.repo = None
            self.repourl = '%s//%s%s' % (uc.scheme, uc.netloc, \
                                         uc.path + args['p'])
        if args['h'] and not self.commit:
            self.commit = args['h']
        del self.message['X-Git-Url']

    def get_pathname(self, dir=None):
        if self.message and self.message['Subject']:
            fn = PatchOps.safe_filename(self.message['Subject'])
            if dir:
                fn = dir + os.sep + fn
            return fn
        else:
            raise InvalidPatchException("Patch contains no Subject line")

    def find_repo(self):
        if self.message['Git-repo'] or self.in_mainline:
            return True

        if self.message['X-Git-Url']:
            self.parse_commitdiff_header()
            return True

        if self.commit:
            commit = None
            for repo in self.repo_list:
                commit = PatchOps.get_commit(self.commit, repo, self.force)
                if commit:
                    r = self.repourl
                    if not r:
                            r = PatchOps.get_git_repo_url(self.repo)
                    if r and r in self.mainline_repo_list:
                        self.in_mainline = True
                    else:
                        self.repo = repo
                    return True

        return False

    def extract(self, paths):
        text = ""
        chunk = ""
        for line in self.message.get_payload().splitlines():
            if _patch_start_re.match(line):
                text += chunk
                chunk = ""
            chunk += line + "\n"

        text += chunk
        return text

    def header(self):
        in_body = False
        ret = ""
        for line in self.message.get_payload().splitlines():
            if not in_body:
                if _patch_start_re.match(line):
                    in_body = True
                    continue
                ret += line + "\n"
            else:
                break
        return ret

    def body(self):
        in_body = False
        ret = ""
        for line in self.message.get_payload().splitlines():
            if not in_body:
                if _patch_start_re.match(line):
                    in_body = True
                    ret += line + "\n"
            else:
                ret += line + "\n"
        return ret

    @staticmethod
    def file_in_path(file, paths):
        for f in paths:
            if f[len(f)-1] == '/' and re.match(f, file):
                return True
        return False

    @staticmethod
    def shrink_chunk(chunk):
        n = -1
        text = ""
        start = -1
        end = -1
        lines = []
        added = 0
        removed = 0
        count = 0
        lines = chunk.splitlines()
        debug = False
        for line in lines:
            n += 1
            if re.match("^-", line):
                if start < 0:
                    start = n - 3 # count this line
                    if start < 0:
                        if debug:
                            print "resetting start(1) (%d, %d)" % (start, n)
                            print "----"
                            print chunk
                            print "----"
                        start = 0

                removed += 1
                count = 0
            elif re.match("^\+", line):
                if start < 0:
                    start = n - 3 # count this line
                    if start < 0:
                        if debug:
                            print "resetting start(2) (%d, %d)" % (start, n)
                            print "----"
                            print chunk
                            print "----"
                        start = 0

                added += 1
                count = 0
            else:
                count += 1
                if start >= 0 and end < 0 and (count > 3 or n +1 == len(lines)):
                    end = n # count this line
                    if end >= len(lines):
                        if debug:
                            print "Truncating end"
                            print "----"
                            print chunk
                            print "----"
                        end = len(lines) - 1

            if start >= 0 and end >= 0:
                diff = end - start
                text +=  "@@ -%d,%d +%d,%d @@\n" % \
                    (start + 1, diff - added, start + 1, diff - removed)
                text += string.join(lines[start:end] , "\n")
                text += '\n'
                end = -1
                start = -1
                added = 0
                removed = 0

        return text

    def handle_merge(self):
        body = ""
        chunk = ""
        text = ""
        
        in_chunk = False
        in_patch = False
        lines = self.body().splitlines()
        for line in lines:
            if _patch_start_re.match(line):
                if in_chunk:
                    text += Patch.shrink_chunk(chunk)
                    chunk = ""
                else:
                    chunk += line + "\n"
                in_patch = True
                in_chunk = False
            elif re.match("^@@@", line):
                if in_chunk:
                    text += Patch.shrink_chunk(chunk)
                else:
                    text += chunk
                chunk = ""
                in_chunk = True
            else:
                if in_chunk:
                    if line[1] == ' ' or line[1] == '+':
                        chunk += line[0:1] + line[2:] + "\n"
                else:
                    chunk += line + "\n"

        if in_chunk:
            text += Patch.shrink_chunk(chunk)
        else:
            text += chunk

        self.message.set_payload(self.header() + text)

    def filter(self, files):
        is_empty = False
        body = ""
        chunk = ""
        file = None
        partial = False
        for line in self.body().splitlines():
            if _patch_start_re.match(line):
                if file and Patch.file_in_path(file, files):
                    body += chunk + "\n"
                elif file:
                    partial = True
                file = None
                chunk = ""
            chunk += line + "\n"

            m = re.match("^\+\+\+ [^/]+/(\S+)", line)
            if m:
                file = m.group(1)

        if file and Patch.file_in_path(file, files):
            body += chunk + "\n"

        self.message.set_payload(self.header() + body)

        if body == "":
            is_empty = True

        if partial:
            commit = self.message['Git-commit']
            self.message.replace_header('Git-commit', '%s (partial)' % commit)
            self.message['Patch-filtered'] = string.join(files, ' ')

        self.update_diffstat()

        if is_empty:
            raise EmptyCommitException("commit is empty")

    def update_refs(self, refs):
        if not 'References' in self.message:
            self.message.add_header('References', refs)
        else:
            self.message['References'] = refs

# for testing this module
if __name__ == '__main__':
    p = Patch('50e9efd60b213ce43ad6979bfc18e25eec2d8413',
              [".",
               "/alt/linux/linux-2.6",
               "/alt/linux/scsi",
               "/alt/public_projects/tgt"],
              ["/alt/linux/linux-2.6",
               "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux-2.6.git",
               "/alt/linux/scsi",
               "git://git.kernel.org/pub/scm/linux/kernel/git/jejb/scsi.git"])
    p.find_commit()

    print "Files:", p.files()
