#!/usr/bin/env python
"""
Support package for doing SUSE Patch operations
"""

from patch.PatchOps import PatchOps
import re
import os
import email.parser
import urllib
from urlparse import urlparse
from patch import mainline_repos, repos



_patch_start_re = re.compile("^(---|\*\*\*|Index:)[ \t][^ \t]|^diff -|^index [0-9a-f]{7}")



class Patch:
    def __init__(self, commit=None, repo=None):
        self.commit = commit
        self.repo = repo
        self.repourl = None
        self.message = None
        self.in_mainline = False

        if repo in mainline_repos:
            self.in_mainline = True

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

    def add_acked_by(self):
        for line in self.message.get_payload().splitlines():
            if re.search("Acked-by.*lduncan@suse", line) or \
               re.search("Signed-off-by.*lduncan@suse", line):
                return

        text = ""
        for line in self.message.get_payload().splitlines():
            if re.match("^---$", line):
                text = text.rstrip() + "\n"
                text += "Acked-by: Lee Duncan <lduncan@suse.com>\n"
            text += line + "\n"

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

        if self.repo in mainline_repos:
            self.in_mainline = True
        elif self.repo and not self.message['Git-repo']:
            r = self.repourl
            if not r:
                    r = PatchOps.get_git_repo_url(self.repo)
            if r and r not in mainline_repos:
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
            for repo in repos:
                commit = PatchOps.get_commit(self.commit, repo)
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
            raise Exception("X-Git-Url provided but is not a URL (%s)" % url)

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
            raise Exception("No subject line")

    def find_repo(self):
        if self.message['Git-repo'] or self.in_mainline:
            return True

        if self.message['X-Git-Url']:
            self.parse_commitdiff_header()
            return True

        if self.commit:
            commit = None
            for repo in repos:
                commit = PatchOps.get_commit(self.commit, repo)
                if commit:
                    r = self.repourl
                    if not r:
                            r = PatchOps.get_git_repo_url(self.repo)
                    if r and r in mainline_repos:
                        self.in_mainline = True
                    else:
                        self.repo = repo
                    return True

        return False

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

    def filter(self, files):
        body = ""
        chunk = ""
        file = ""
        for line in self.body().splitlines():
            if _patch_start_re.match(line):
                if file in files:
                    body += chunk + "\n"
                file = ""
                chunk = ""
            chunk += line + "\n"
            m = re.match("^\+\+\+ [^/]+/(\S+)", line)
            if m:
                file = m.group(1)

        if file in files:
            body += chunk + "\n"

        self.message.set_payload(self.header() + body)

        self.update_diffstat()

    def update_refs(self, refs):
        if not 'References' in self.message:
            self.message.add_header('References', refs)
        else:
            self.message['References'] = refs

# for testing this module
if __name__ == '__main__':
    p = Patch('50e9efd60b213ce43ad6979bfc18e25eec2d8413')
    p.find_commit()

    print p.files()
