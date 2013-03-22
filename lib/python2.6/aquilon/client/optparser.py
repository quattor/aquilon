#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Option parsing for the aq client."""

import sys
import os

if __name__ == '__main__':
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    sys.path.append(BINDIR)

    import aquilon.client.depends


from optparse import OptionParser, OptionValueError
from lxml import etree
from subprocess import Popen
import re
import textwrap

# The code is not exactly pretty. If you want to improve it, here are some
# suggestions:
# - Integrate error handling with the parser
# - Merge the CustomParser and OptParser classes
# - Investigate using argparse instead of optparse - we don't need anything
#   fancy from the parser, but there may be some niceties in argparse
# - Rework the check() logic; make it call parser.error() instead of printing
#   the help on its own
# - Get rid of the shortHelp() and recursiveHelp() methods once every command
#   has a man page written in DocBook


def cmdName():
    return os.path.basename(sys.argv[0])


def read_file(option, opt, value, parser):
    try:
        with open(value) as f:
            setattr(parser.values, option.dest, f.read())
    except Exception, e:
        raise OptionValueError("Error opening '%s' for %s: %s" %
                               (value, opt, e))


def get_term_width():
    width = None
    try:
        import fcntl, termios, struct
        # The help is printed to stderr, so only check that for being a terminal
        if os.isatty(sys.stderr.fileno()):
            res = fcntl.ioctl(sys.stderr.fileno(), termios.TIOCGWINSZ,
                              struct.pack("HHHH", 0, 0, 0, 0))
            width = struct.unpack("HHHH", res)[1]
    except:
        pass
    if width is None:
        try:
            width = int(os.environ["COLUMNS"])
        except:
            pass
    if width is None or width < 80:
        width = 80
    return width


def normalize_help(data):
    asciidata = ""
    if data.strip():
        asciidata = data.encode()
    if len(asciidata) == 0:
        return ""
    asciidata = re.sub('^\s*', '', asciidata)
    asciidata = re.sub('[\s\r]*$', '', asciidata)
    asciidata = re.sub('^\s+$', '', asciidata)
    asciidata = re.sub('\s+', ' ', asciidata)

    asciidata = asciidata.replace('%prog', cmdName())
    return asciidata


class CustomParser(OptionParser):

    def __init__(self, command, *args, **kwargs):
        self.command = command
        # OptionParser is an old-style class, so super() does not work
        OptionParser.__init__(self, *args, **kwargs)

    def print_help(self, file=None):
        # Check if the command has a man page
        use_man = False
        with open("/dev/null", "w") as devnull:
            p = Popen(["man", "-W", self.command.name], stdout=devnull,
                      stderr=devnull)
            p.communicate()
            if p.returncode == 0:
                use_man = True

        if use_man:
            p = Popen(["man", self.command.name])
            p.communicate()
            exit(p.returncode)
        else:
            print self.command.recursiveHelp(0, width=get_term_width())


class ParsingError(StandardError):

    def __init__(self, errorMessage, helpMessage=''):
        StandardError.__init__(self)
        self.help = helpMessage
        self.error = errorMessage

    def get(self):
        return self.error, self.help

    def __repr__(self):
        return "Parsing Error: " + self.error


class Element(object):

    def __init__(self, node):
        self.node = node
        if "name" in node.attrib:
            self.name = node.attrib["name"]
        else:
            self.name = ""

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)

    def check(self, options):
        return None, False


class Command(Element):

    def __init__(self, node):
        Element.__init__(self, node)
        self.optgroups = []
        self.transports = []

        for child in node:
            if child.tag == 'p':
                pass
            elif child.tag == 'optgroup':
                self.optgroups.append(OptGroup(child))
            elif child.tag == 'transport':
                self.transports.append(Transport(child))
            elif child.tag == etree.Comment:
                pass
            else:
                raise ParsingError("Unexpected tag <%s> inside <command>" %
                                   child.tag)

    def check(self, options):
        result = {}
        for optgroup in self.optgroups:
            try:
                (res, found) = optgroup.check(options)
            except ParsingError, e:
                e.help = self.recursiveHelp(0, width=get_term_width())
                raise e
            result.update(res)
        # check for conflicts
        conflicts = self.getAllConflicts(result)
        for conflict, option in conflicts.items():
            if conflict in result:
                raise ParsingError("Option or option group %s "
                                   "conflicts with %s" %
                                   (option, conflict))

        transport = None
        for t in self.transports:
            if t.trigger is None and transport is None:
                transport = t
                continue
            if t.trigger is not None and t.trigger in result:
                transport = t
                continue

        return transport, result

    def genOptions(self, parser):
        for o in self.optgroups:
            o.genOptions(parser)

    def getAllConflicts(self, found):
        conflicts = {}
        for g in self.optgroups:
            c = g.getAllConflicts(found)
            conflicts.update(c)
        return conflicts

    def shortHelp(self, width=None):
        lines = textwrap.wrap(" ".join([o.shortHelp() for o in self.optgroups]),
                              width)

        if len(lines) > 0:
            return "\n".join([lines[0]] + ["    " + l for l in lines[1:]])
        else:
            return ""

    def recursiveHelp(self, indentlevel, width=None):
        cmd = cmdName() + " "
        if self.name != "*":
            cmd += self.name.replace("_", " ") + " "
        shortwidth = width - len(cmd) if width else None
        cmd += self.shortHelp(width=shortwidth)
        res = cmd + "\n\n"

        paragraphs = [normalize_help(self.node.text)]
        for child in self.node:
            if child.tag != 'p':
                continue
            paragraphs.append(normalize_help(child.tail))

        formatted = []
        for para in paragraphs:
            lines = "\n".join(["    " + l for l in textwrap.wrap(para, width - 4)])
            formatted.append(lines)
        res += "\n\n".join(formatted) + "\n\n"

        for og in self.optgroups:
            res += og.recursiveHelp(indentlevel + 1, width=width) + "\n"

        return res


class OptGroup(Element):

    def __init__(self, node):
        Element.__init__(self, node)
        self.help = ''
        self.options = []

        if "mandatory" in node.attrib:
            self.mandatory = node.attrib["mandatory"].lower() == "true"
        else:
            self.mandatory = False

        if "fields" in node.attrib:
            self.fields = node.attrib["fields"]
        else:
            self.fields = 'none'

        if "conflicts" in node.attrib:
            self.conflicts = node.attrib["conflicts"].split(' ')
        else:
            self.conflicts = []

        for child in node:
            if child.tag == "option":
                self.options.append(Option(child))
            elif child.tag == "optgroup":
                self.options.append(OptGroup(child))
            elif child.tag == etree.Comment:
                pass
            else:
                raise ParsingError("Unexpected tag <%s> inside <optgroup>" %
                                   child.tag)

    def check(self, options):
        result = {}
        found = {}
        foundany = False
        foundall = True

        for option in self.options:
            (res, f) = option.check(options)
            found[option.name] = f
            if f:
                result.update(res)
            foundany = foundany or f
            foundall = foundall and f

        # check if the options are specified as requested
        if self.mandatory:
            if self.fields == 'all' and not foundall:
                raise ParsingError('Not all mandatory options specified!')
            if self.fields == 'any' and not foundany:
                raise ParsingError('Please provide any of the required options!')
            if not foundany:
                raise ParsingError('Mandatory options not provided')
        else:
            if self.fields == 'all' and foundany and not foundall:
                raise ParsingError('Not all mandatory options specified!')

        # return result
        return result, foundany

    def genOptions(self, parser):
        for o in self.options:
            o.genOptions(parser)

    def getAllConflicts(self, found):
        conflicts = {}
        for o in self.options:
            c = o.getAllConflicts(found)
            conflicts.update(c)
        for conflict in self.conflicts:
            conflicts[conflict] = self.name
        return conflicts

    def shortHelp(self):
        return " ".join([o.shortHelp() for o in self.options])

    def recursiveHelp(self, indentlevel, width=None):
        if self.mandatory:
            help = "Requires %s of these options:\n" % self.fields
        else:
            if self.fields == 'all':
                help = "Optional, but must use all or none:\n"
            else:
                help = "Optional:\n"

        whitespace = " " * (4 * (indentlevel))
        res = whitespace + help
        width -= 4 * indentlevel
        for o in self.options:
            res += o.recursiveHelp(indentlevel + 1, width=width)
        return res


class Option(Element):

    def __init__(self, node):
        Element.__init__(self, node)

        if "type" in node.attrib:
            self.type = node.attrib["type"]
        else:
            self.type = 'string'

        if "reverse" in node.attrib:
            if self.type != "boolean":
                raise ParsingError("The reverse attribute only makes sense "
                                   "for boolean options.")
            self.reverse = node.attrib["reverse"]
        else:
            if self.type == "boolean":
                self.reverse = "no" + self.name
            else:
                self.reverse = None

        if "short" in node.attrib:
            self.short = node.attrib["short"]
        else:
            self.short = None

        if "mandatory" in node.attrib:
            self.mandatory = node.attrib["mandatory"].lower() == "true"
        else:
            self.mandatory = False

        if "conflicts" in node.attrib:
            self.conflicts = node.attrib["conflicts"].split(' ')
        else:
            self.conflicts = []

        if "default" in node.attrib:
            if self.type == "boolean" or self.type == "flag":
                if node.attrib["default"].lower() == "true":
                    self.default = True
                elif node.attrib["default"].lower() == "false":
                    self.default = False
                else:
                    raise ParsingError("Invalid boolean default for %s" %
                                       self.name)
            elif self.type == "int":
                self.default = int(node.attrib["default"])
            else:
                self.default = node.attrib["default"]
        else:
            self.default = None

    def check(self, options):
        result = {}
        found = False

        if self.mandatory:
            if not hasattr(options, self.name):
                raise ParsingError('Option ' + self.name + ' is missing')
        if hasattr(options, self.name):
            val = getattr(options, self.name)
            if not val is None:
                found = True
            result[self.name] = getattr(options, self.name)
#        if self.mandatory and not found:
#            raise ParsingError(self.node.text, 'Option '+self.name+' is mandatory but it was not specified')
        return result, found

    def genOptions(self, parser):
        if parser.has_option('--' + self.name):
            return
        names = ["--" + self.name]
        if self.short:
            names.append("-" + self.short)

        extra_args = {}

        if self.default:
            extra_args["default"] = self.default

        if self.type == 'boolean':
            parser.add_option(*names, dest=self.name, action="store_true",
                              **extra_args)
            parser.add_option("--" + self.reverse, dest=self.name,
                              action="store_false")
        elif self.type == "flag":
            parser.add_option(*names, dest=self.name, action="store_true",
                              **extra_args)
        elif self.type in ['string', 'ipv4', 'mac']:
            parser.add_option(*names, dest=self.name, action="store",
                              **extra_args)
        elif self.type == 'int':
            parser.add_option(*names, dest=self.name, action="store",
                              type="int", **extra_args)
        elif self.type == 'float':
            parser.add_option(*names, dest=self.name, action="store",
                              type="float", **extra_args)
        elif self.type == 'file' or self.type == 'list':
            # Need type?
            parser.add_option(*names, dest=self.name, action="callback",
                              callback=read_file, type="string")
        elif self.type == 'multiple':
            parser.add_option(*names, dest=self.name, action="append")
        else:
            raise ParsingError('Invalid option type: ' + self.type)

    def getAllConflicts(self, found):
        """Return any conflicts(keys) and the original option (values)."""
        conflicts = {}
        if self.name in found:
            for conflict in self.conflicts:
                conflicts[conflict] = self.name
        return conflicts

    def shortHelp(self):
        if self.type == "boolean":
            if self.reverse == "no" + self.name:
                return "--[no]" + self.name
            else:
                return "--%s|--%s" % (self.name, self.reverse)
        elif self.type in ["string", "file", "list", "int"]:
            return "--" + self.name + " " + self.name.upper()
        else:
            return "--" + self.name

    def recursiveHelp(self, indentlevel, width=None):
        whitespace = " " * (4 * indentlevel)
        help = normalize_help(self.node.text)
        if self.default is not None:
            help += "\nDefault: %s" % self.default

        helplines = textwrap.wrap(help, width - 36)
        res = whitespace + "%*s %s\n" % (-35 + 4 * indentlevel,
                                         self.shortHelp(), helplines[0])
        for line in helplines[1:]:
            res = res + " " * 36 + line + "\n"

        return res


class Transport(Element):

    def __init__(self, node):
        Element.__init__(self, node)
        self.method = node.attrib["method"]
        self.path = node.attrib["path"]
        self.trigger = "trigger" in node.attrib and node.attrib["trigger"] or None
        self.expect = "expect" in node.attrib and node.attrib["expect"] or None
        self.custom = "custom" in node.attrib and node.attrib["custom"] or None


class OptParser(object):

    def __init__(self, filename):
        handle = open(filename)
        self.tree = etree.parse(handle)

    def parse(self, args):
        # Get the command
        command_words = []
        opt_idx = len(args)
        for idx, arg in enumerate(args):
            if arg[0] == '-':
                opt_idx = idx
                break
            command_words.append(arg)
        command = '_'.join(command_words)
        options = args[opt_idx:]

        # Convert "help foo" to "foo --help"
        if command.startswith("help_"):
            command = command[5:]
            options = ["--help"]

        # The global options are listed at the '*' pseudo-command
        nodelist = self.tree.xpath("/commandline/command[@name='*']")
        if not nodelist:
            raise ParsingError("input.xml is invalid",
                               "Global options are missing")
        global_node = nodelist[0]

        nodelist = self.tree.xpath("/commandline/command[@name='%s']" % command)
        if not nodelist:
            self.unknown_command(command)

        return self.handle_command(nodelist[0], global_node, options)

    def unknown_command(self, command):
        width = get_term_width()

        helpmsg = []
        helpmsg.append("Available commands are:")
        helpmsg.append("")

        commands = []
        for node in self.tree.getiterator("command"):
            name = node.get("name")
            if name != "*":
                commands.append(name)

        commands.sort()

        maxlen = max([len(s) for s in commands]) + 4
        columns = (width - 4) / maxlen
        rows = len(commands) / columns + 1

        for row in xrange(rows):
            res = "    "
            for column in xrange(columns):
                if column * rows + row < len(commands):
                    res += "%-*s" % (maxlen, commands[column * rows + row])
            helpmsg.append(res)

        helpmsg.append("")
        helpmsg.append("You can get more help with")
        helpmsg.append("aq help COMMAND")
        helpmsg.append("  or")
        helpmsg.append("aq COMMAND --help")

        if command == "help":
            print "\n".join(helpmsg)
            exit(0)
        elif command:
            errmsg = "Command %s is not known!" % command
        else:
            errmsg = "Please specify a command."

        # The previous code used OptParser.error() which exits with return code
        # 2, but now we don't have the parser created yet
        print >>sys.stderr, "%s\n\nError: %s" % ("\n".join(helpmsg), errmsg)
        sys.exit(2)

    def handle_command(self, cmd_node, global_node, options):
        glb = Command(global_node)
        cmd = Command(cmd_node)

        prog = "%s %s" % (cmdName(), cmd.name)
        self.parser = CustomParser(cmd, conflict_handler='resolve', prog=prog)
        self.parser.add_option('--help', '-h', action='help', default=False)

        # "verbose" and "quiet" are connected, and this cannot be expressed
        # correctly in input.xml
        self.parser.add_option('--verbose', '-v', action='store_true',
                               default=True)
        self.parser.add_option('--quiet', '-q', dest='verbose',
                               action='store_false')

        glb.genOptions(self.parser)
        cmd.genOptions(self.parser)

        opts, args = self.parser.parse_args(options)
        if args:
            raise ParsingError("Extra arguments on the command line")

        try:
            dummy, global_options = glb.check(opts)
            transport, command_options = cmd.check(opts)
        except ParsingError, e:
            self.parser.set_usage(e.help)
            self.parser.error(e.error)
        return cmd.name, transport, command_options, global_options


if __name__ == '__main__':
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    p = OptParser(os.path.join(BINDIR, '..', '..', '..', '..', 'etc', 'input.xml'))
    try:
        (command, transport, commandOptions, globalOptions) = p.parse(sys.argv[1:])
    except ParsingError, e:
        print "ERROR", e.error
    else:
        print "Command:", command
        print "Command Options:", commandOptions
        print "Global Options:", globalOptions
