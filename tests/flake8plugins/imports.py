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

from collections import defaultdict


def flake8wrapper(f):
    f.name = __name__
    f.version = '0.0.1'
    f.skip_on_py3 = False
    f.off_by_default = False
    return f


@flake8wrapper
def one_import_per_line(logical_line, tokens, filename, noqa):
    # Check if QA has to be skipped
    if noqa:
        return

    # Check if the logical line contains something
    split_line = logical_line.split()
    if len(split_line) < 1:
        return

    # Check if the logical line is an import
    if not split_line[0] in ('import', 'from'):
        return

    # Check if the logical line contains only one import
    pos = logical_line.find(',')
    if pos == -1:
        return

    # Build the physical lines from the tokens of the logical line, we
    # will also build a dict associating each line with its position in
    # the logical line
    previous_line = None
    physical_lines = {}
    token_seen = defaultdict(lambda: 0)
    token_to_pos = {}
    line_to_pos = {}
    for t in tokens:
        pos = logical_line.find(t.string)
        if pos != -1:
            for i in range(0, token_seen[t.string]):
                pos = pos + logical_line[pos + 1:].find(t.string)
        token_seen[t.string] += 1
        token_to_pos[t] = pos

        if pos == -1:
            # If the token represents a comment, we want to clean-up the line
            # from it for the work we need to do later
            if t.type == 54 and previous_line is not None and \
                    t.start[0] == previous_line:
                line = t.line[:t.start[1]] + t.line[t.end[1]:]
                physical_lines[t.start[0]] = line

            # If we did not compute a position for the token, we won't
            # be able to do anything else anyway...
            continue

        if t.start[0] != previous_line:
            previous_line = t.start[0]
            line_to_pos[t.start[0]] = [pos, pos + len(t.string)]
            physical_lines[t.start[0]] = t.line
        elif previous_line is not None:
            line_to_pos[previous_line][1] = pos + len(t.string)

    # If we reach here and we are not multiline
    # AQD401: Do not import more than one module per line
    if len(physical_lines) == 1:
        yield pos, 'AQD401 one import per line'
        return

    # AQD402: only 'from ... import' can be multiline
    if split_line[0] == 'import':
        yield pos, 'AQD402 only \'from ... import\' can be multiline'
        return

    # Find the opening of the import
    lefttok = None
    pkgtok = None
    importtok = None
    for i, t in enumerate(tokens):
        if t.type != 1:
            continue

        if t.string == 'import':
            if len(tokens) <= i + 1:
                # Import line finishing by import? Some other checker would
                # have reported the issue
                return

            importtok = t
            lefttok = tokens[i + 1:]
            break
        elif t.string != 'from':
            pkgtok = t

    if lefttok is None:
        # A from block without an import after? Some other checker would have
        # reported the issue
        return

    if lefttok[0].string != '(':
        # AQD403: multiline 'from ... import' have to enclose the
        #         imported modules in parenthesis
        yield token_to_pos[importtok] + len(importtok.string), (
            'AQD403 multiline \'from ... import\' have to enclose '
            'the imported modules in parenthesis')

    # Check all the tokens that are after the 'import', and store the
    # 'NAME'-type tokens in a dict with line numbers as keys and token
    # strings and positions as values, we take the occasion to also check
    # AQD407: modules of a multiline 'from ... import' should be imported in
    #         alphabetical order
    pos = 0
    per_line = {}
    previous = None
    blank_line = False
    for t in lefttok:
        if t.type == 55 and t.string == t.line:
            # If we reach here, we just encountered a blank line
            blank_line = True
            continue

        if t.type == 1:
            per_line.setdefault(t.start[0], []).append(t)

            # Check AQD407, but ignore it if there is a blank line between the
            # previous import and this one
            if not blank_line and previous and \
                    previous.string.lower() > t.string.lower():
                yield token_to_pos[t], (
                    'AQD407 imports not in alphabetical '
                    'order ({0}.{1}, {0}.{2})'.format(
                        pkgtok.string, previous.string, t.string))
            previous = t

            # As we just have seen a 'NAME'-type token, we have cancelled the
            # effects of the previous blank line as to ignore the alphabetical
            # order in between the element just before the blank line and the
            # element just after
            blank_line = False

    # AQD404: no module should be imported on the first line of a multiline
    #         'from ... import'
    if tokens[0].start[0] in per_line:
        yield token_to_pos[per_line[tokens[0].start[0]][0]], (
            'AQD404 no module should be imported on the first line of a '
            'multiline \'from ... import\'')

    # AQD405: no module should be imported on the last line of a multiline
    #         'from ... import' (only applies if the last token itself is
    #         not a module imported, is useful to enforce the use of a
    #         closing parenthesis on its own line)
    if tokens[-1].type != 1 and tokens[-1].start[0] in per_line:
        yield token_to_pos[per_line[tokens[-1].start[0]][0]], (
            'AQD405 no module should be imported on the last line of a '
            'multiline \'from ... import\'')

    # AQD401 to be applied in a multiline 'from ... import'
    for _, mtokens in sorted(per_line.items()):
        if len(mtokens) > 1:
            yield token_to_pos[mtokens[0]], 'AQD401 one import per line'

    # Now we want to check that each physical line containing a module
    # to import is actually ending with a ','
    # AQD406: every import of a multiline 'from ... import'
    #         should end with a ','
    for lineno in sorted(per_line.keys()):
        if lineno == tokens[-1].start[0]:
            # Skip if it's the same line as the last token, as for instance
            # the following structure might be authorized depending on which
            # rules are enabled:
            #    from xxx import (aaa,
            #                     bbb)
            # And in this case, we wouldn't want to have a ',' at the end
            continue

        line = physical_lines.get(lineno)
        if line is not None and not line.rstrip().endswith(','):
            yield line_to_pos[lineno][1], (
                'AQD406 every import of a multiline \'from ... import\' '
                'should end with a \',\'')
