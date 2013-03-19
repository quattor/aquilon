#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2013  Contributor
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

"""
Small utility to populate static objects (i.e. those that do not have plenary
templates) in the database.
"""

import os
import sys
import logging
from shlex import shlex
from inspect import isclass

import utils
utils.load_classpath()

import argparse

from aquilon.exceptions_ import ArgumentError, NotFoundException
from sqlalchemy.exc import IntegrityError
import aquilon.aqdb.model
from aquilon.aqdb.db_factory import DbFactory

# Add a nice error reporting function to shlex
class Lexer(shlex):
    def __init__(self, filename):
        self.filename = filename
        self.macros = {}

        input = file(filename, 'rt')
        return shlex.__init__(self, input, posix=True)

    def error(self, message):
        raise ValueError("%s %s" % (self.error_leader(self.filename), message))

def parse_object(session, lexer, lookup=False, verbose=False):
    """
    Parse an object definition

    If lookup is True, the object must exist; otherwise it is created.
    """

    token = lexer.get_token()
    if not token:
        return None

    # Handle macro creation and lookup
    if token == "@":
        token = lexer.get_token()
        if not token:
            lexer.error("macro name expected.")

        if lookup:
            if token not in lexer.macros:
                lexer.error("macro @%s is not defined." % token)
            return lexer.macros[token]
        else:
            if token in lexer.macros:
                lexer.error("macro @%s is already defined." % token)
            obj = parse_object(session, lexer, lookup=True, verbose=verbose)
            lexer.macros[token] = obj
            return obj

    if hasattr(aquilon.aqdb.model, token):
        cls = getattr(aquilon.aqdb.model, token)
    else:
        cls = None
    if not cls or not isclass(cls) or not issubclass(cls, aquilon.aqdb.model.Base):
        lexer.error("%s is not a database class." % token)

    token = lexer.get_token()
    if token != "(":
        lexer.error("'(' is expected.")

    # parse_params() may call parse_objectr() recursively
    params = parse_params(session, lexer, verbose=verbose)

    try:
        if lookup:
            obj = cls.get_unique(session, compel=True, **params)
        else:
            if verbose:
                print "Adding %s(%r)." % (cls.__name__, params)
            try:
                obj = cls(**params)
                session.add(obj)
                session.flush()
                session.expire(obj)
            except IntegrityError, err:
                lexer.error(err)
    except ArgumentError, err:
        lexer.error(err)
    except NotFoundException, err:
        lexer.error(err)
    return obj

def parse_params(session, lexer, verbose=False):
    """ Parse an object parameter list """

    params = {}

    while True:
        name = lexer.get_token()
        if not name:
            lexer.error("field name expected.")

        token = lexer.get_token()
        if token != "=":
            lexer.error("'=' expected.")

        token = lexer.get_token()

        object_lookup = False
        if token == "@":
            object_lookup = True
        elif hasattr(aquilon.aqdb.model, token):
            cls = getattr(aquilon.aqdb.model, token)
            if isclass(cls) and issubclass(cls, aquilon.aqdb.model.Base):
                object_lookup = True

        if object_lookup:
            lexer.push_token(token)
            value = parse_object(session, lexer, lookup=True, verbose=verbose)
        else:
            value = token

            # Try to recognize booleans and numbers
            if value == "True":
                value = True
            elif value == "False":
                value = False
            elif value == "None":
                value = None
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass

        params[name] = value

        token = lexer.get_token()
        if token == ")":
            break
        elif token == ",":
            pass
        else:
            lexer.error("',' or ')' expected.")
    return params

def load_from_file(session, filename, verbose=False):
    lexer = Lexer(filename)
    try:
        while parse_object(session, lexer, verbose=verbose) is not None:
            pass
    except ValueError, err:
        session.rollback()
        raise SystemExit(err)
    except Exception:
        print("%s caught exception, bailing out." %
              lexer.error_leader(lexer.filename))
        session.rollback()
        raise

    session.commit()

if __name__ == '__main__':
    logging.basicConfig(levl=logging.ERROR)

    parser = argparse.ArgumentParser(description="Loads initial data to aqdb")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose mode; show objects as they are added")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Enable debug mode; show SQL queries")
    parser.add_argument("-f", "--file", action="store", required=True,
                        help="Name of the input file")
    opts = parser.parse_args()

    if opts.debug:
        log = logging.getLogger('sqlalchemy.engine')
        log.setLevel(logging.INFO)

    db = DbFactory(verbose=opts.verbose)
    aquilon.aqdb.model.Base.metadata.bind = db.engine
    session = db.Session()

    load_from_file(session, opts.file, verbose=opts.verbose)
