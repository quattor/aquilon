#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""  The discriminator for Locations """
import sys
sys.path.append('../..')
#from aqdbBase import aqdbBase
#from db_factory import db_factory
from db import meta, engine, Base
import subtypes as st

LocationType  = st.subtype('LocationType','location_type')
location_type = LocationType.__table__

_loc_types = ['company', 'hub', 'continent', 'country', 'city', 'bucket',
              'building', 'rack', 'chassis', 'desk', 'base_location_type']

if __name__ == '__main__':
    #dbf = db_factory()
    #aqdbBase.metadata.bind = dbf.engine
    location_type.create(checkfirst=True)

    st.populate_subtype(LocationType, _loc_types)
