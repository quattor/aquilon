#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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

import argparse
from collections import defaultdict
from contextlib import contextmanager
import os
import re
import shutil
import site
import sys
import tempfile

TESTDIR = os.path.dirname(__file__)
LIBDIR = os.path.realpath(os.path.join(TESTDIR, '..', 'lib'))

site.addsitedir(LIBDIR)

# Any of the above may override the default location for ms.version...
try:
    import ms.version
except ImportError:
    pass
else:
    ms.version.addpkg('setuptools', '36.7.0')

    # For GitPython
    ms.version.addpkg('GitPython', '2.1.5')
    ms.version.addpkg('gitdb', '0.6.4')
    ms.version.addpkg('smmap', '0.8.3')

    try:
        ms.version.addpkg('ms.modulecmd', '1.0.6')
        import ms.modulecmd
        # To load git, as it's required by GitPython
        ms.modulecmd.load('msde/git/2.9.5')
    except Exception:
        pass

    # For PEP8
    ms.version.addpkg('pycodestyle', '2.3.1')

    # For flake8
    ms.version.addpkg('flake8', '3.4.1')
    ms.version.addpkg('enum34', '1.1.6')
    ms.version.addpkg('configparser', '3.5.0b2')
    ms.version.addpkg('pyflakes', '1.5.0')
    ms.version.addpkg('mccabe', '0.6.1')

    ms.version.addpkg('hacking', '1.1.0')
    ms.version.addpkg('pbr', '3.1.1')
    ms.version.addpkg('six', '1.11.0-ms1')

    ms.version.addpkg('flake8_per_file_ignores', '0.6')
    ms.version.addpkg('pathmatch', '0.2.1')
    ms.version.addpkg('typing', '3.6.2')

    # To pretty print with colors
    ms.version.addpkg('termcolor', '1.1.0')
    ms.version.addpkg('colorama', '0.3.7')

import colorama
from flake8.api import legacy as flake8
import termcolor


class DictReport(object):
    def __init__(self, *args, **kwargs):
        super(DictReport, self).__init__(*args, **kwargs)
        self.__errors = []

    def save_error(self, filename, code, row, col, text):
        self.__errors.append({
            'path': filename,
            'code': code,
            'row': row,
            'col': col,
            'text': text,
        })

    @staticmethod
    def __error_sorter(k):
        return (
            k['path'].lower(),
            k['row'],
            k['col'],
            k['code'],
        )

    def get_errors(self):
        self.__errors.sort(key=self.__error_sorter)
        return self.__errors


class Flake8DictReport(DictReport, flake8.formatter.BaseFormatter):

    _regex_clean_code = re.compile('^([A-Z][0-9]*)[^0-9]*$')

    def __init__(self, options):
        super(Flake8DictReport, self).__init__(options)

    def format(self, error):
        self.save_error(
            filename=error.filename,
            code=self._regex_clean_code.sub('\g<1>', error.code),
            row=error.line_number,
            col=error.column_number,
            text=error.text,
        )


class CheckerHandler(object):

    def __init__(self, git_dir, **kwargs):
        self._dir = git_dir

    @staticmethod
    def file_matches(filename):
        return filename.endswith('.py')

    def relpath(self, path):
        return path

    @contextmanager
    def get_files(self):
        files = []

        for wroot, wdirs, wfiles in os.walk(self._dir):
            for f in wfiles:
                if self.file_matches(f):
                    files.append(os.path.join(wroot, f))

        yield files

    def is_affected(self, line, path, code):
        return True


class CheckerHandlerCommits(CheckerHandler):

    _regex_blame_line = re.compile(
        '^(?P<commit>[a-z0-9]*) '
        '(?P<file>.*\.py) +'
        '(?P<line>[0-9]+)\) '
        '(?P<content>.*)$')

    def __init__(self, from_ref, to_ref, git_dir, current, **kwargs):
        self._from_ref = from_ref
        self._to_ref = to_ref
        self._git_dir = git_dir
        self._current = current

        # No tmp dir for now
        self._tmpdir = None

        # Prepare the git repository
        self._repo = git.Repo(git_dir)

        # Get all commits between those commits
        ancestor = self._repo.merge_base(from_ref, to_ref)
        if not ancestor:
            raise RuntimeError('Unable to find ancestor for '
                               'refs {} and {}'.format(
                                   from_ref, to_ref))
        ancestor = ancestor[0].hexsha
        self._commits = self._repo.git.rev_list(
            '--ancestry-path', '{}..{}'.format(
                ancestor, to_ref)).splitlines()

        # Initialize the empty cache
        self._affected_lines_cache = {}

    @contextmanager
    def _get_diff_files(self, diff_args, show_ref):
        if not self._current:
            self._tmpdir = tempfile.mkdtemp(
                prefix='{}-'.format(os.path.basename(__file__)))
        try:
            files = []
            for f in self._repo.git.diff(*diff_args).splitlines():
                if not self.file_matches(f):
                    continue

                if self._current:
                    # When using current, we can use the file as-is, we do not
                    # need to get the version of the file at the time of the
                    # 'to' reference
                    files.append(f)
                    continue

                dirname = os.path.dirname(f)
                if dirname != '.':
                    tmpdirname = os.path.join(self._tmpdir, dirname)
                    try:
                        os.makedirs(tmpdirname)
                    except OSError:
                        if not os.path.isdir(tmpdirname):
                            raise

                copiedf = os.path.join(self._tmpdir, f)
                fcontent = self._repo.git.show('{}:{}'.format(show_ref, f))
                with open(copiedf, 'w+') as fh:
                    fh.write(fcontent)
                    fh.write('\n')  # git show seems to be hiding the last \n
                files.append(copiedf)

            yield files
        finally:
            if self._tmpdir:
                shutil.rmtree(self._tmpdir)

    @contextmanager
    def get_files(self):
        args = [
            '--name-only', '--diff-filter=ACM',
            self._from_ref, self._to_ref,
        ]
        with self._get_diff_files(diff_args=args, show_ref=self._to_ref) as f:
            yield f

    def relpath(self, path):
        if not self._tmpdir:
            return path
        return os.path.relpath(path, self._tmpdir)

    def get_affected_lines(self, path):
        if path not in self._affected_lines_cache:
            lines = {}
            blame = self._repo.git.blame(
                '-l', '-s', '-f', self._to_ref, '--', path).splitlines()
            for line in blame:
                commit = line.split(' ', 1)[0]
                if commit not in self._commits:
                    continue

                m = self._regex_blame_line.search(line)
                if m:
                    lines[int(m.group('line'))] = commit
            self._affected_lines_cache[path] = lines
        return self._affected_lines_cache[path]

    def consider_lines(self, line, code):
        lines = [line, ]

        # The H306 error is only shown on the second of the two lines
        # affected. This means that if we have a H306 error/warning on
        # a given line, we need to also consider it if we modified the
        # previous line
        if code == 'H306':
            lines.append(line - 1)

        return lines

    def is_affected(self, line, path, code):
        for l in self.consider_lines(line, code):
            affected = self.get_affected_lines(path).get(l)
            if affected:
                return affected
        return False


class CheckerHandlerStaged(CheckerHandlerCommits):

    _regex_diff_block = re.compile(
        '@@ -(?P<linebef>[0-9]+),(?P<nlinebef>[0-9]+) '
        '\+(?P<lineaf>[0-9]+),(?P<nlineaf>[0-9]+) @@'
        '[^\n]*\n(?P<patch>.*?)(?=@@ |$)', re.DOTALL)

    def __init__(self, git_dir, current, **kwargs):
        self._current = current

        # No tmp dir for now
        self._tmpdir = None

        # Prepare the git repository
        self._repo = git.Repo(git_dir)

        # Initialize the empty cache
        self._affected_lines_cache = {}

    @contextmanager
    def get_files(self):
        args = [
            '--cached', '--name-only', '--diff-filter=ACM',
        ]
        with self._get_diff_files(diff_args=args, show_ref='') as f:
            yield f

    def get_affected_lines(self, path):
        if path not in self._affected_lines_cache:
            # Get the staged diff for the given path, and compute the lines
            # that are currently staged so we can only consider those in
            # the results of the code style check
            staged = self._repo.git.diff(
                '--cached', '--diff-filter=ACM', '--', path)
            lines = {}
            for m in self._regex_diff_block.finditer(staged):
                block = m.groupdict()
                curline = int(block['lineaf'])
                discardedlines = 0
                for lineno, line in enumerate(block['patch'].splitlines()):
                    if line.startswith('-'):
                        discardedlines += 1
                    elif line.startswith('+'):
                        lines[curline + lineno - discardedlines] = True
            self._affected_lines_cache[path] = lines
        return self._affected_lines_cache[path]


def run():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--from',
        dest='from_ref',
        help='Consider the changes from this reference (default: {to}^)',
    )
    parser.add_argument(
        '--to',
        dest='to_ref',
        help='Consider the changes up to this reference (default: HEAD)',
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        default=False,
        help=('Check all current files instead of only the ones affected '
              'by specific commits'),
    )
    parser.add_argument(
        '--current',
        action='store_true',
        default=False,
        help=('Check the files affected between the references, but using '
              'their current content'),
    )
    parser.add_argument(
        '--staged', '--cached',
        action='store_true',
        default=False,
        help=('Check the files staged to be committed; useful to run '
              'that script in a pre-commit hook'),
    )
    parser.add_argument(
        '--git-bin',
        help='Specify the path to the git binary to be used',
    )
    parser.add_argument(
        '--git-dir',
        default='.',
        help='The path to the git directory (default: current working dir)',
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        default=False,
        help='Add statistics on the error codes',
    )
    args = parser.parse_args()

    # Check that the options received are compatible with each other
    if args.all:
        if args.from_ref or args.to_ref or args.current or args.staged:
            parser.error('Cannot use --all together with '
                         '--staged/--current/--from/--to')
    elif args.staged:
        if args.from_ref or args.to_ref:
            parser.error('Cannot use --staged together with '
                         '--current/--from/--to')
    else:
        if not args.to_ref:
            args.to_ref = 'HEAD'
        if not args.from_ref:
            args.from_ref = '{}^'.format(args.to_ref)

    # If provided, set the path to the git binary for GitPython
    if args.git_bin is not None:
        os.environ['GIT_PYTHON_GIT_EXECUTABLE'] = os.path.abspath(args.git_bin)
    # The following is done to insure that we import git only after setting
    # the environment variable to specify the path to the git bin received on
    # the command line
    global git
    import git

    # Move to the git directory
    os.chdir(args.git_dir)

    # Prepare the Flake8 checker
    flake8style = flake8.get_style_guide(
        quiet=True,
        # No need to select or ignore anything, it should pick-up the project
        # configuration when run from the project directory
    )
    flake8style.init_report(reporter=Flake8DictReport)

    if args.all:
        checkerhandler_cls = CheckerHandler
    elif args.staged:
        checkerhandler_cls = CheckerHandlerStaged
    else:
        checkerhandler_cls = CheckerHandlerCommits
    checkerhandler = checkerhandler_cls(**vars(args))

    with checkerhandler.get_files() as files:
        if not files:
            print('No affected files')
            return

        # Run the flake8 checker against our files
        flake8result = flake8style.check_files(files)

    # We want to use colors to make the error messages
    # clearer, so we need to init colorama for cross
    # platform support
    colorama.init()
    colon = termcolor.colored(
        ':',
        'cyan',
    )
    error_types = (
        ('E', 'PEP8 error'),
        ('W', 'PEP8 warning'),
        ('F', 'pyflakes error'),
        ('H', 'hacking error'),
    )

    def print_results(result, prefix=None):
        errors = defaultdict(lambda: 0)
        tot_errors = defaultdict(lambda: 0)
        if args.stats:
            stats = defaultdict(lambda: 0)

        # Go through the errors
        for error in result.get_errors():
            tot_errors[error['code'][0]] += 1

            # Only consider this error if it is introduced in the change
            path = checkerhandler.relpath(error['path'])
            affected = checkerhandler.is_affected(
                error['row'], path, error['code'])
            if not affected:
                continue

            errors[error['code'][0]] += 1
            if args.stats:
                stats[error['code']] += 1

            print(
                (
                    '{path}'
                    '{colon}'
                    '{row}'
                    '{colon}'
                    '{col}'
                    '{colon}'
                    '{code}'
                    '{colon}'
                    '{affected}'
                    '{text}'
                ).format(
                    colon=colon,
                    affected='' if affected is True else '{}{}'.format(
                        termcolor.colored(
                            affected[:7],
                            'blue',
                        ), colon),
                    path=termcolor.colored(
                        path,
                        'magenta',
                    ),
                    row=termcolor.colored(
                        error['row'],
                        'green',
                    ),
                    col=termcolor.colored(
                        error['col'],
                        'yellow',
                    ),
                    code=termcolor.colored(
                        error['code'],
                        'red',
                    ),
                    text=error['text'],
                )
            )

        print('{}{}{} in the affected files'.format(
            '{}: '.format(prefix) if prefix else '',
            '' if args.all else 'Introduced ',
            ', '.join('{}/{} {}(s)'.format(errors[k], tot_errors[k], n)
                      for k, n in error_types)))

        if args.stats:
            print('Stats:')
            for k, v in sorted(stats.items()):
                print('  - {}: {}'.format(k, v))

        return sum(errors.values())

    errors = print_results(
        flake8result._application.formatter, prefix='Flake8')
    sys.exit(min(1, errors))


def init():
    if __name__ == '__main__':
        run()


init()
