#!/ms/dist/python/PROJ/core/2.5.0/bin/python
"""Class and Table for ip addresses"""

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Table

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.column_types.ipv4  import IPV4

class IpAddress(Base):
    """ ip address table. KISS as we'll build up MANY different 
    relations into this table (a_name -> m2m <- IP, 
                                iface -> m2m <- IP )  
    """

    ip_address = Column(IPV4, primary_key=True)
    #TODO: have network as a property, but it's really just a call out to sql

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

