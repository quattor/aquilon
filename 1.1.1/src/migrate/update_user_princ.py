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
    #FILL_ME_IN

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
