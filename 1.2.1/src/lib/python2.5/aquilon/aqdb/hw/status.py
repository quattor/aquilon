#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Status is an overloaded term, but we use it to represent various stages of
    deployment, such as production, QA, dev, etc. each of which are also
    overloaded terms... """
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))

from db_factory import monkeypatch
from table_types.name_table import make_name_class

Status = make_name_class('Status','status')
status = Status.__table__

@monkeypatch(Status)
def __init__(self,name):
    e = "Status is a static table and can't be instanced, only queried."
    raise ArgumentError(e)

@monkeypatch(Status)
def __repr__(self):
    return str(self.name)

def populate():
    #FIX ME
    if empty(status):
        i=status.insert()
        for name in ['prod','dev','qa','build']:
            i.execute(name=name)
