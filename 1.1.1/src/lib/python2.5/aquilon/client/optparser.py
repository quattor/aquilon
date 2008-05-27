#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

from optparse import OptionParser
from xml.parsers import expat
import re
import pdb


def joinDict (d1, d2):
    temp = d1
    for k,v in d2.iteritems():
        if (not temp.has_key(k)):
            temp[k] = v
    return temp

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
            result = joinDict(result, res)
        return result, True

# --------------------------------------------------------------------------- #

    def recursiveHelp (self):
        res = self.help
        for child in self.children:
            res = res + child.recursiveHelp()
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

    def check (self, command, options):
        result = {}

        if (command is None):
            if (self.__allcommands):
                ##print "check generic options"
                (res, found) = self.__allcommands.check(command, options)
                result = joinDict(result,res)
            return None, result

        if (command.find('help') != -1):
            helpfor = command[5:]
            if (self.__commandlist.has_key(helpfor)):
                print self.__commandlist[helpfor].recursiveHelp()
                exit(1)
            else:
                if helpfor:
                    print "The command '%s' is not known to this server." % helpfor
                print "Available commands are:"
                k = self.__commandlist.keys()
                k.sort()
                for c in k:
                    print "\t", self.__commandlist[c].name
                exit(1)

        if (self.__commandlist.has_key(command)):
            ##print "commandline checking command:", command
            commandElement = self.__commandlist[command]
            (res, found) = commandElement.check(command, options)
            result = joinDict (result,res)
        elif (command == 'help' or command == ''):
            # print general help, and help for each command
            raise ParsingError ('',self.recursiveHelp())
        else:
            raise ParsingError('Command '+command+' is not known!',self.recursiveHelp())

        transport = None
        for t in commandElement.transports:
            if t.trigger is None and transport is None:
                transport = t
                continue
            if t.trigger is not None and result.has_key(t.trigger):
                transport = t
                continue

        return transport, result

# --------------------------------------------------------------------------- #

    def recursiveHelp (self):
        res = self.help + "\nValid commands are:\n"
        for k in self.__commandlist.keys():
            res = res + self.__commandlist[k].recursiveHelp()
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
                e.help = self.recursiveHelp()
                raise e
            result = joinDict (result, res)
        return result, True

# --------------------------------------------------------------------------- #

    def recursiveHelp (self):
        res = "\n"
        lines = self.help.split("\n")
        for line in lines:
            res = res + "    " + line + "\n"
        for og in self.optgroups:
            res = res + og.recursiveHelp()
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
            self.help = "    Requires %s of these options:\n" % self.fields
        else:
            if self.fields == 'all':
                self.help = "    Optional, but must use all or none:\n"
            else:
                self.help = "    Optional:\n"

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
                result = joinDict(result, res)
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

        # check for conflicts
        for option in self.options:
            if not found[option.name]:
                continue
            for conflict in option.conflicts:
                if (found.has_key(conflict) and found[conflict] == True):
                    raise ParsingError('Option or option group '+option.name+' conflicts with '+conflict)
        # return result
        return result, foundany

# --------------------------------------------------------------------------- #

    def recursiveHelp (self):
        res = self.help
        for o in self.options:
            res = res + o.recursiveHelp()
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

    def genOption (self, parser):
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

    def recursiveHelp (self):
        LLEN = 80
        val = self.type=='string' and " VALUE" or ""
        help = len(self.help)>1 and self.help or "\n"
        res = "    --%-20s %s" %(self.name+val, help)
        if (len(res) < LLEN):
            return res
        pos = res.rfind(" ", 0, LLEN)
        if (pos > 0):
            tres = res[0:res.rfind(" ", 0, LLEN)]
            res = res[res.rfind(" ", 0, LLEN):]
        else:
            tres = res[0:LLEN]
            res = res[LLEN:]
        while (len(res) >= LLEN - 26):
            pos = res.rfind(" ", 0, LLEN-26)
            if (pos > 0):
                tres = tres + "\n" + " "*26 + res[0:pos]
                res = res[pos:]
            else:
                tres = tres + "\n" + " "*26 + res[0:LLEN-26]
                res = res[LLEN-26:]
        if (len(res) > 1):
            tres = tres + "\n" + " "*26 + res
        else:
            tres = tres + "\n"
        return tres

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
            element.genOption (self.parser)
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
        if (self.__nodeStack):
            parent = self.__nodeStack[-1]
            parent.help = parent.help + asciidata + "\n"
        else:
            self.__root.help = self.root.help + asciidata + "\n"

# --------------------------------------------------------------------------- #

    def ParseXml(self, filename):
        Parser = expat.ParserCreate( )
        Parser.StartElementHandler = self.StartElement
        Parser.EndElementHandler = self.EndElement
        Parser.CharacterDataHandler = self.CharacterData
        ParserStatus = Parser.Parse(open(filename).read( ), 1)

# --------------------------------------------------------------------------- #

    def getOptions (self):
        (opts, args) = self.parser.parse_args()
        if (opts.help):
            print self.__root.recursiveHelp ()
            exit(1)
        elif (not args):
            self.parser.usage = self.__root.recursiveHelp ()
            self.parser.error('Please specify a command')
        else:
            command = '_'.join(args)

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
