#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Dependencies for migration (note use of 0.5beta instead of 4.6) """
import sys
from datetime import datetime

import msversion

msversion.addpkg('sqlalchemy', '0.5beta', 'dev')
msversion.addpkg('sqlalchemy-migrate','0.4.4','dev')
msversion.addpkg('ipython', '0.8.2', 'dist')
msversion.addpkg('cx-Oracle','4.3.3-10.2.0.1-py25','dist')

from sqlalchemy import (MetaData, create_engine, PrimaryKeyConstraint,
                        UniqueConstraint, ForeignKey, Table, Column, Sequence,
                        Integer, Index, DateTime, String, PassiveDefault)

from sqlalchemy.orm import sessionmaker, scoped_session, deferred, relation
from sqlalchemy.sql import insert, text, func, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exceptions import SQLError, DatabaseError

Base = declarative_base()

#FIX ME: this is really primative. Make debug.py actually control ipshell() and
#    it's behavior in the next version of admin

if '-d' not in sys.argv:
    from IPython.Shell import IPShellEmbed
    ipshell = IPShellEmbed()

from admin.column_defaults import *
