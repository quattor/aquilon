#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import sys
import os
from subprocess import Popen, PIPE
from datetime import date

# Could act like a quine and take this info from the bits above.
# Going in the other direction and having this file update itself. :)

shebang = "#!/usr/bin/env python\n"

ex_re = re.compile(r'^\s*#\s*ex:')
ex_line = "# ex: set expandtab softtabstop=4 shiftwidth=4: \n"
emacs_re = re.compile(r'^\s+#\s+-\*- ')
emacs_line = "# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-\n"

comment_line = "#\n"
comment_prefix = "# "
comment_re = re.compile(r'^\s*#')
whitespace_re = re.compile(r'^\s*$')

license = """
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
license_re = re.compile(r'^#\s*' + license.splitlines()[1])
license = [comment_prefix + line + '\n' for line in license.splitlines()]

year = str(date.today().year)
copyright_line = "%sCopyright (C) %s  Contributor\n" % (comment_prefix, year)
copyright_re = re.compile(r'^\s*#\s*Copyright')
contributor_copyright_re = re.compile(
    r'^\s*#\s*Copyright\s+\([Cc]\)\s+([\d\s,]+)\s+(Contributor|Morgan Stanley)')

trailing_space_re = re.compile(r'\s+(?=\n)$')
module_re = re.compile(r'^\s*#\s*This module is part of [Aa]quilon')


def fix_file(filepath):
    with file(filepath) as f:
        contents = f.readlines()
    if not contents:
        return
    # Segregate the top from the rest of the file
    last_leading_comment = -1
    for i in range(len(contents)):
        if comment_re.search(contents[i]):
            last_leading_comment = i
            continue
        break
    #print >>sys.stderr, "Using %d as last leading comment line." % last_leading_comment

    current_copyright_line = copyright_line
    # Find the copyright line.
    for line in contents:
        if copyright_re.search(line):
            current_copyright_line = line
            break

    # If this is someone else's copyright, don't mess with the file
    if not contributor_copyright_re.search(current_copyright_line):
        sys.stderr.write("Skipping %s because of unrecognized copyright.\n" %
                         filepath)
        return

    # If the copyright line needs to be fixed, fix it.
    # We get the relevent copyright years by checking the git logs.
    # git log --format=format:"%ad" --date=short -- ./path.py | cut -d- -f1 | sort | uniq
    p1 = Popen(["git", "log", "--format=format:%ad", "--date=short",
                "--follow", "--", filepath],
               stdout=PIPE, stderr=2)
    p2 = Popen(["cut", "-d-", "-f1"], stdin=p1.stdout, stdout=PIPE, stderr=2)
    p3 = Popen(["sort"], stdin=p2.stdout, stdout=PIPE, stderr=2)
    p4 = Popen(["uniq"], stdin=p3.stdout, stdout=PIPE, stderr=2)
    copyright_years = p4.communicate()[0].splitlines() or [year]

    is_python = filepath.endswith(".py")

    new_contents = []
    # If there's a shebang, standardize it
    if contents[0].startswith("#!"):
        if "python" in contents[0]:
            new_contents.append(shebang)
            is_python = True
        else:
            new_contents.append(contents[0])

    # The editor settings apply to Python code only
    if is_python:
        new_contents.append(emacs_line)
        new_contents.append(ex_line)

    new_contents.append(comment_line)
    new_contents.append("%sCopyright (C) %s  Contributor\n" %
                        (comment_prefix, ",".join(copyright_years)))
    new_contents.extend(license)

    # clean trailing spaces...
    new_contents = [trailing_space_re.sub("", line) for line in new_contents]

    # Leave any other unwanted cruft out of the file (ex line)
    for i in range(last_leading_comment + 1, len(contents)):
        line = contents[i]
        if ex_re.search(line) or emacs_re.search(line):
            #print >>sys.stderr, "Skipping ex line"
            continue
        if copyright_re.search(line):
            #print >>sys.stderr, "Skipping copyright line"
            continue
        if module_re.search(line):
            #print >>sys.stderr, "Skipping module line"
            continue
        new_contents.append(line)

    if contents == new_contents:
        return
    else:
        with file(filepath, 'w') as f:
            f.writelines(new_contents)


def fix_recursive(start_dir):
    print >>sys.stderr, "Processing %s" % start_dir
    for dirpath, dirnames, filenames in os.walk(start_dir):
        if '.git' in dirnames:
            dirnames.remove('.git')
        for f in filenames:
            full_path = os.path.join(dirpath, f)
            if not f.endswith('.py') and not os.access(full_path, os.X_OK):
                continue
            fix_file(full_path)


def main(args):
    if len(args) > 2:
        print >>sys.stderr, \
                "Takes only one argument, the root directory to process."
        sys.exit(1)
    if len(args) < 2:
        start_dir = os.path.join(os.path.dirname(os.path.realpath(args[0])),
                                 "..")
    else:
        start_dir = args[1]
    fix_recursive(start_dir)

if __name__ == '__main__':
    main(sys.argv)
