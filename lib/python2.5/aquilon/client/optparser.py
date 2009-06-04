#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Option parsing for the aq client."""


from optparse import OptionParser
from xml.parsers import expat
import os
import sys
import re
import textwrap
import pdb


def cmdName():
    return os.path.basename(sys.argv[0])

# =========================================================================== #

class ParsingError(StandardError):
    def __init__ (self, errorMessage, helpMessage = ''):
        self.help = helpMessage
        self.error = errorMessage

# --------------------------------------------------------------------------- #

    def get (self):
        return self.error, self.help

# --------------------------------------------------------------------------- #

    def __repr__(self):
        return "Parsing Error: " + self.error

# =========================================================================== #

class Element(object):
    def __init__ (self, name, attributes):
        self.help = ''
        self.name = ''
        self.children = []

# --------------------------------------------------------------------------- #

    def add (self, element):
        self.children.append(element)

# --------------------------------------------------------------------------- #

    def check (self, command, options):
        result = {}
        for child in self.children:
            (res, found) = child.check(command, options)
            result.update(res)
        return result, True

# --------------------------------------------------------------------------- #

    def recursiveHelp (self, indentlevel):
        res = self.help

        for child in self.children:
            res = res + child.recursiveHelp(indentlevel)
        return res

# =========================================================================== #

class commandline(Element):
    def __init__ (self, name, attributes):
        Element.__init__(self, name, attributes)
        self.__commandlist = {}
        self.__allcommands = None

# --------------------------------------------------------------------------- #

    def add (self, element):
        if (element.name == "*"):
            self.__allcommands = element
        else:
            self.__commandlist[element.name] = element;

# --------------------------------------------------------------------------- #

    def populateParser(self, command, parser):
        # add global options
        self.__allcommands.genOptions(parser)

        if command in self.__commandlist:
            # add command-specific options
            self.__commandlist[command].genOptions(parser)
            # and set command-specific usage message
            parser.usage = self.__commandlist[command].recursiveHelp(0)
        else:
            parser.usage = self.__allcommands.recursiveHelp(0)
        
# --------------------------------------------------------------------------- #

    def commandList(self):
        res = self.help + "\nGlobal options:\n" + self.__allcommands.recursiveHelp(0)
        res += "Available commands are:"

        commands = self.__commandlist.keys()
        commands.sort()
        maxlen = max([len(s) for s in commands]) + 4
        columns = 75 / maxlen
        rows = len(commands) / columns + 1

        for row in xrange(rows):
            res += "\n    "
            for column in xrange(columns):
                if column * rows + row < len(commands):
                    res = res + "%-*s" % (maxlen, commands[column * rows + row])

        res += "\n\nYou can get more help with\n"
        res += cmdName() + " help COMMAND\n  or\n" + cmdName() + " COMMAND --help\n"

        return res

# --------------------------------------------------------------------------- #

    def check (self, command, options):

        # check generic options
        if (command is None):
            if (self.__allcommands):
                ##print "check generic options"
                (res, found) = self.__allcommands.check(command, options)
            return None, res

        # handle help pseudocommand
        if (command.find('help') != -1):
            helpfor = command[5:]
            if (self.__commandlist.has_key(helpfor)):
                print self.__commandlist[helpfor].recursiveHelp(0)
                exit(0)
            else:
                if helpfor:
                    print "The command '%s' is not known to this server." % helpfor
                print self.commandList()
                exit(0)

        if (self.__commandlist.has_key(command)):
            ##print "commandline checking command:", command

            # print help if --help is on the command line
            if options.help:
                print self.__commandlist[command].recursiveHelp(0)
                exit(0)

            commandElement = self.__commandlist[command]
            (res, found) = commandElement.check(command, options)
        else:
            raise ParsingError('Command '+command+' is not known!',self.commandList())

        transport = None
        for t in commandElement.transports:
            if t.trigger is None and transport is None:
                transport = t
                continue
            if t.trigger is not None and res.has_key(t.trigger):
                transport = t
                continue

        return transport, res

# --------------------------------------------------------------------------- #

    def recursiveHelp(self, indentlevel):
        res = self.help
        res += "\nGlobal options:\n" + self.__allcommands.recursiveHelp(indentlevel)
        res += "\nValid commands are:\n"
        for k in self.__commandlist.keys():
            res = res + self.__commandlist[k].recursiveHelp(indentlevel)
        return res

# --------------------------------------------------------------------------- #

    def checkGlobal (self, options):
        result = {}

# =========================================================================== #

class command(Element):
    def __init__ (self, name, attributes):
        Element.__init__(self, name, attributes)
        self.name = attributes['name']
        self.optgroups = []
        #self.help = '%prog ' + self.name + '\n'
        self.transports = []

# --------------------------------------------------------------------------- #

    def add (self, element):
        if ( isinstance( element, optgroup ) ):
            self.optgroups.append(element);
        elif ( isinstance( element, transport ) ):
            self.transports.append(element)
        # Silently drop anything else...

# --------------------------------------------------------------------------- #

    def check (self, command, options):
        result = {}
        for optgroup in self.optgroups:
            try:
                (res, found) = optgroup.check(command, options)
            except ParsingError, e:
                e.help = self.recursiveHelp(0)
                raise e
            result.update(res)
        # check for conflicts
        conflicts = self.getAllConflicts(result)
        for (conflict, option) in conflicts.items():
            if result.has_key(conflict):
                raise ParsingError("Option or option group %s "
                                   "conflicts with %s" %
                                   (option, conflict))
        return result, True

# --------------------------------------------------------------------------- #

    def genOptions(self, parser):
        for o in self.optgroups:
            o.genOptions(parser)

# --------------------------------------------------------------------------- #

    def getAllConflicts(self, found):
        conflicts = {}
        for g in self.optgroups:
            c = g.getAllConflicts(found)
            conflicts.update(c)
        return conflicts

# --------------------------------------------------------------------------- #

    def shortHelp(self):
        lines = textwrap.wrap(" ".join([ o.shortHelp() for o in self.optgroups ]))

        if len(lines) > 0:
            return "\n".join([lines[0]] + [ "    " + l for l in lines[1:] ])
        else:
            return ""
        

# --------------------------------------------------------------------------- #

    def recursiveHelp(self, indentlevel):
        cmd = cmdName() + " "
        if self.name != "*":
            cmd += self.name.replace("_", " ") + " "
        cmd += self.shortHelp()
        res = cmd + "\n\n"

        if (len(self.help) > 0):
            res = res + "\n".join(["    " + l for l in textwrap.wrap(self.help)]) + "\n\n"

        for og in self.optgroups:
            res = res + og.recursiveHelp(indentlevel + 1) + "\n"

        return res

# =========================================================================== #

class optgroup(Element):
    def __init__ (self, name, attributes):
        Element.__init__(self, name, attributes)
        self.name = attributes['name']
        self.help = ''
        self.options = []

        if (attributes.has_key('mandatory')):
            try:
                self.mandatory = eval (attributes['mandatory'])
            except StandardError, e:
                self.mandatory = False
        else:
            self.mandatory = False

        if (attributes.has_key('fields')):
            self.fields = attributes['fields']
        else:
            self.fields = 'none'

        if self.mandatory:
            self.help = "Requires %s of these options:\n" % self.fields
        else:
            if self.fields == 'all':
                self.help = "Optional, but must use all or none:\n"
            else:
                self.help = "Optional:\n"

        if (attributes.has_key('conflicts')):
            self.conflicts = attributes['conflicts'].split(' ')
        else:
            self.conflicts = []

# --------------------------------------------------------------------------- #

    def add (self, element):
        self.options.append(element);

# --------------------------------------------------------------------------- #

    def check (self, command, options):
        result   = {}
        found    = {}
        foundany = False
        foundall = True

        for option in self.options:
            (res, f) = option.check(command, options)
            found[option.name] = f
            if (f):
                result.update(res)
            foundany = foundany or f
            foundall = foundall and f

        # check if the options are specified as requested
        if (self.mandatory):
            if (self.fields == 'all' and not foundall):
                raise ParsingError('Not all mandatory options specified!')
            if (self.fields == 'any' and not foundany):
                raise ParsingError('Please provide any of the required options!')
            if (not foundany):
                raise ParsingError('Mandatory options not provided')
        else:
            if (self.fields == 'all' and foundany and not foundall):
                raise ParsingError('Not all mandatory options specified!')

        # return result
        return result, foundany

# --------------------------------------------------------------------------- #

    def genOptions(self, parser):
        for o in self.options:
            o.genOptions(parser)

# --------------------------------------------------------------------------- #

    def getAllConflicts(self, found):
        conflicts = {}
        for o in self.options:
            c = o.getAllConflicts(found)
            conflicts.update(c)
        for conflict in self.conflicts:
            conflicts[conflict] = self.name
        return conflicts

# --------------------------------------------------------------------------- #

    def shortHelp(self):
        return " ".join([o.shortHelp() for o in self.options])

# --------------------------------------------------------------------------- #

    def recursiveHelp(self, indentlevel):
        whitespace = " " * (4 * (indentlevel))
        res = whitespace + self.help
        for o in self.options:
            res += o.recursiveHelp(indentlevel + 1)
        return res

# =========================================================================== #

class option(Element):
    def __init__ (self, name, attributes):
        Element.__init__(self, name, attributes)
        self.name = attributes['name']
        if (attributes.has_key('type')):
            self.type = attributes['type']
        else:
            self.type = 'string'

        if (attributes.has_key('short')):
            self.short= attributes['short']
        else:
            self.short = None

        if (attributes.has_key('mandatory')):
            self.mandatory = eval(attributes['mandatory'])
        else:
            self.mandatory = False

        if (attributes.has_key('conflicts')):
            self.conflicts = attributes['conflicts'].split(' ')
        else:
            self.conflicts = []

        self.help = ''

# --------------------------------------------------------------------------- #

    def add (self, element):
        pass

# --------------------------------------------------------------------------- #

    def check (self, command, options):
        result = {}
        found = False

        if (self.mandatory):
            if (not hasattr(options, self.name)):
                raise ParsingError ('Option '+self.name+' is missing');
        if (hasattr(options, self.name)):
            val = getattr(options, self.name)
            if (not val is None):
                found = True
            result[self.name] = getattr(options, self.name);
#        if (self.mandatory and not found):
#            raise ParsingError (self.help, 'Option '+self.name+' is mandatory but it was not specified')
        return result, found

# --------------------------------------------------------------------------- #

    def genOptions(self, parser):
        if (parser.has_option('--'+self.name)):
            return
        if (self.short):
            str = 'parser.add_option("-'+self.short+'", "--'+self.name+'", dest="'+self.name+'"'
        else:
            str = 'parser.add_option("--'+self.name+'", dest="'+self.name+'"'
        if (self.type == 'boolean'):
            str = str+', action="store_true"'
        elif (self.type == 'string'):
            str = str+', action="store"'
        elif (self.type == 'multiple'):
            str = str +', action="append"'
        else:
            raise ParsingError('Invalid option type: '+self.type);
        str = str+')'
        eval (str)

# --------------------------------------------------------------------------- #

    def getAllConflicts(self, found):
        """Return any conflicts (keys) and the original option (values)."""
        conflicts = {}
        if self.name in found:
            for conflict in self.conflicts:
                conflicts[conflict] = self.name
        return conflicts

# --------------------------------------------------------------------------- #

    def shortHelp(self):
        return "--" + self.name + ("" if self.type != "string" else " " + self.name.upper())

# --------------------------------------------------------------------------- #

    def recursiveHelp(self, indentlevel):
        whitespace = " " * (4 * indentlevel)
        help = self.help if len(self.help) else "\n"

        helplines = textwrap.wrap(help, 40)
        res = whitespace + "%*s %s\n" % (-35 + 4 * indentlevel, self.shortHelp(), helplines[0])
        for line in helplines[1:]:
            res = res + " " * 36 + line + "\n"

        return res

# =========================================================================== #

class transport(Element):
    def __init__ (self, name, attributes):
        Element.__init__(self, name, attributes)
        self.method = attributes['method']
        self.path = attributes['path']
        self.trigger = attributes.has_key('trigger') and attributes['trigger'] or None
        self.expect = attributes.has_key('expect') and attributes['expect'] or None
        self.custom = attributes.has_key('custom') and attributes['custom'] or None

# =========================================================================== #

class OptParser (object):
    def __init__ (self, xmlFileName):
        self.__nodeStack = []
        self.__root = None
        self.parser = OptionParser (conflict_handler='resolve')
        self.parser.add_option('--help', '-h', action='store_true', default=False)
        self.ParseXml(xmlFileName)

# --------------------------------------------------------------------------- #

    def StartElement(self, name, attributes):
        import types
        'Expat start element event handler'
        element = None

        if (name == "commandline"):
            element = commandline(name, attributes)
        elif (name == "command"):
            element = command(name, attributes)
        elif (name == "optgroup"):
            element = optgroup(name, attributes)
        elif (name == "option"):
            element = option(name, attributes)
        elif (name == "transport"):
            element = transport(name, attributes)
        else:
            element = Element(name, attributes)

        if (self.__nodeStack):
            parent = self.__nodeStack[-1]
            parent.add(element)
        else:
            self.__root = element

        self.__nodeStack.append(element)

# --------------------------------------------------------------------------- #

    def EndElement(self, name):
        'Expat end element event handler'
        self.__nodeStack.pop( )

# --------------------------------------------------------------------------- #

    def CharacterData(self, data):
        'Expat character data event handler'
        asciidata = "" 
        if data.strip():
            asciidata = data.encode()
        if (len(asciidata) == 0):
            return
        asciidata = re.sub('^\s*','', asciidata)
        asciidata = re.sub('[\s\r]*$','', asciidata)
        asciidata = re.sub('^\s+$','', asciidata)

        asciidata = asciidata.replace('%prog', cmdName() )

        if (self.__nodeStack):
            parent = self.__nodeStack[-1]
            parent.help = parent.help + asciidata + "\n"
        else:
            self.__root.help = self.__root.help + asciidata + "\n"

# --------------------------------------------------------------------------- #

    def ParseXml(self, filename):
        Parser = expat.ParserCreate( )
        Parser.StartElementHandler = self.StartElement
        Parser.EndElementHandler = self.EndElement
        Parser.CharacterDataHandler = self.CharacterData
        ParserStatus = Parser.Parse(open(filename).read(), 1)

# --------------------------------------------------------------------------- #

    def getOptions(self):
        # get command
        command_words = []
        for arg in sys.argv[1:]:
            if arg[0] == '-': break
            command_words.append(arg)
        command = '_'.join(command_words)

        self.__root.populateParser(command, self.parser)
        (opts, args) = self.parser.parse_args()

        if (not args):
            if opts.help:
                # verbose help if we were given no command but have --help
                self.parser.usage = self.__root.recursiveHelp(0)
            else:
                self.parser.usage = self.__root.commandList()

            self.parser.error('Please specify a command')

        try:
            this_is_None, globalOptions = self.__root.check(None, opts)
            transport, commandOptions = self.__root.check(command, opts)
        except ParsingError, e:
            self.parser.usage = e.help
            self.parser.error(e.error)
        return command, transport, commandOptions, globalOptions

# =========================================================================== #


if __name__ == '__main__':
    import sys, os
    BINDIR = os.path.dirname( os.path.realpath(sys.argv[0]) )
    p = OptParser( os.path.join( BINDIR, '..', '..', '..', '..', 'etc', 'input.xml' ) )
    try:
 #       pdb.set_trace()
        (command, transport, commandOptions, globalOptions) = p.getOptions()
    except ParsingError, e:
        print "ERROR", e.error
 #       print "HELP\n", e.help
    else:
        print "Command:", command
        print "Command Options:", commandOptions
        print "Global Options:", globalOptions


