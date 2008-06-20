#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""  The discriminator for Network and Storage Interfaces """

import sys
import sys
sys.path.insert(0,'..')
sys.path.insert(1,'../..')
sys.path.insert(2,'../../..')

import subtypes as st

dstr = """ AQDB will support different types of interfaces besides just the
        usual physical type. Other kinds in the environment include zebra,
        service, heartbeat, router, mgmt/ipmi, vlan/802.1q, build. At the moment
        we;re only implementing physical, with zebra and 802.1Q likely to be
        next"""

InterfaceType  = st.subtype('InterfaceType','interface_type',dstr)
interface_type = InterfaceType.__table__

_iface_types = ['base_interface_type','physical','zebra','service','802.1q',
            'hba']

#st.populate_subtype(InterfaceType, _iface_types)
