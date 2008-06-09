#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" intended to make the new tables during migration """

from depends import *
import migrate.changeset
from new_tables.role import role
from add_data import get_id

###########   REMOVE WHEN USED AS A LIBRARY   ###
import db_factory                               #
dbf = db_factory.db_factory()                   #
Base.metadata.bind = dbf.engine                 #
m = Base.metadata                               #
#################################################

user_principal = Table('user_principal', m, autoload=True)
col = Column('role_id', Integer,
               ForeignKey('role.id', name='usr_princ_role_fk'))

def upgrade():
    ## ADD NEW ROLE COLUMN
    try:
        col.create(user_principal)
    except DatabaseError, e:
        print >> sys.stderr, e
        #no point in continuing...
        sys.exit(9)

    ##ADD THE ROLE ID DATA...
    # Some of these users might not exist... planning on running
    # `aq permission` later anyway...
    try:
        nobody = get_id("role", "name", "nobody")
        dbf.safe_execute("UPDATE user_principal SET role_id = :role",
                role=nobody)
        aqd_admin = get_id("role", "name", "aqd_admin")
        is1_morgan = get_id("realm", "name", "is1.morgan")
        dbf.safe_execute("UPDATE user_principal SET role_id = :role WHERE realm_id = :realm AND name in ('cdb', 'njw', 'wesleyhe', 'guyroleh', 'daqscott', 'kgreen', 'benjones')",
                role=aqd_admin, realm=is1_morgan)
        engineering = get_id("role", "name", "engineering")
        dbf.safe_execute("UPDATE user_principal SET role_id = :role WHERE realm_id = :realm AND name in ('cesarg', 'jasona', 'dankb', 'goliaa', 'samsh', 'hagberg', 'hookn', 'jelinker', 'kovasck', 'lookerm', 'bet', 'walkert', 'af', 'lillied')",
                role=engineering, realm=is1_morgan)
        operations = get_id("role", "name", "operations")
        dbf.safe_execute("UPDATE user_principal SET role_id = :role WHERE realm_id = :realm AND name in ('nathand', 'premdasr', 'bestc', 'chawlav', 'wbarnes', 'gleasob', 'lchun', 'peteryip', 'richmoj', 'tipping', 'hardyb', 'martinva', 'coroneld')",
                role=operations, realm=is1_morgan)
    except DatabaseError, e:
        print e

    ## ADD NON NULL CONSTRAINT
    #SHOULD BE NO NEED TO ENFORCE THE DEFAULT, aqdb code will do that.
    try:
        col.alter(nullable=False)
    except DatabaseError, e:
        print e


def downgrade():
    ##DROP Column
    try:
        col.drop()
    except DatabaseError, e:
        print e
        sys.exit(9)



if __name__ == '__main__':
    upgrade()
    downgrade()
