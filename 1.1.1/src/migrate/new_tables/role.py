#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Role for authorization, copied from auth.py for migration"""
import sys
sys.path.insert(0,'..')
from depends import *

class Role(Base):
    __table__ = Table('role', Base.metadata,
        Column('id', Integer, Sequence('role_id_seq'),
               primary_key=True),
        Column('name', String(32), nullable=False),
        Column('creation_date', DateTime,
               default = datetime.now, nullable = False),
        Column('comments', String(255), nullable=True),
        PrimaryKeyConstraint('id', name='role_pk'),
        UniqueConstraint('name', name='role_name_uk'))

role = Role.__table__

def populate():
    COMMENT = 'system default roles (auto-populated)'
    ROLES=['nobody','operations','engineering', 'aqd_admin']
    ret_val = []
    ins = role.insert()
    for i in ROLES:
        ret_val.append(role.insert({'name':i,'comments':COMMENT}))
    return ret_val

#select B.name, B.role_id from aqd.user_principal A, user_principal B
#where B.name = A.name(+);
"""
NAME     ROLE_ID
-------- -------
benjones       4
cdb            4
cesarg         3
daqscott       4
goliaa         3
hagberg        3
hookn          3
jasona         3
kgreen         4
njw            4
peteryip       2
wesleyhe       4
gleasob        2
premdasr       2
hardyb         2
kovasck        3
nathand        2
lookerm        3
richmoj        2
af             3
bet            3
lchun          2
wbarnes        2
walkert        3
lillied        3
bestc          2
dankb          3
martinva       2
jelinker       3
tonyc          3
samsh          3
tipping        2
guyroleh       4
chawlav        2

34 rows selected (0.01 seconds)
"""
