#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""TorSwitch formatter."""


from aquilon import const
from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.hw.tor_switch import TorSwitch


class TorSwitchFormatter(ObjectFormatter):
    def format_raw(self, tor_switch, indent=""):
        details = [indent + "%s: %s" %
                (tor_switch.model.machine_type.capitalize(),
                 tor_switch.a_name.fqdn)]
        # This is a bit of a hack.  Delegating out to the standard location
        # formatter now spews too much information about chassis.  Maybe
        # that will change when chassis has a corresponding hardware type.
        for location_type in const.location_types:
            if getattr(tor_switch.location, location_type, None) is not None:
                details.append(indent + "  %s: %s" % (
                                    location_type.capitalize(),
                                    getattr(tor_switch.location, location_type)))
                if location_type == 'rack':
                    details.append(indent + "    Row: %s" %
                                   tor_switch.location.rack.rack_row)
                    details.append(indent + "    Column: %s" %
                                   tor_switch.location.rack.rack_column)
        details.append(self.redirect_raw(tor_switch.model, indent + "  "))
        if tor_switch.serial_no:
            details.append(indent + "  Serial: %s" % tor_switch.serial_no)
        for p in tor_switch.switchport:
            if p.interface:
                details.append(indent + "  Switch Port %d: %s %s %s" %
                        (p.port_number, p.interface.tor_switch.model.machine_type,
                            p.interface.tor_switch.name, p.interface.name))
            else:
                details.append(indent +
                        "  Switch Port %d: No interface recorded in aqdb" %
                        p.port_number)
        for i in tor_switch.interfaces:
            details.append(indent + "  Interface: %s %s %s boot=%s" 
                    % (i.name, i.mac, i.ip, i.bootable))
        if tor_switch.comments:
            details.append(indent + "  Comments: %s" % tor_switch.comments)
        return "\n".join(details)

    def get_header(self):
        """This is just an idea... not used anywhere (yet?)."""
        return "tor_switch,rack,building,vendor,model,serial,interface,mac,ip"

    def format_csv(self, tor_switch):
        """This was implemented specifically for tor_switch.  May need
        to check and do something different for other tor_switch types.
        
        """
        results = []
        details = [tor_switch.a_name.fqdn, tor_switch.location.rack,
                tor_switch.location.building, tor_switch.model.vendor.name,
                tor_switch.model.name, tor_switch.serial_no]
        if not tor_switch.interfaces:
            details.extend([None, None, None])
            results.append(details)
        for i in tor_switch.interfaces:
            full = details[:]
            full.extend([i.name, i.mac, i.ip])
            results.append(full)
        return "\n".join([",".join([str(detail or "") for detail in result])
            for result in results])

ObjectFormatter.handlers[TorSwitch] = TorSwitchFormatter()


class SimpleTorSwitchList(list):
    pass

class SimpleTorSwitchListFormatter(ObjectFormatter):
    def format_raw(self, smlist, indent=""):
        return str("\n".join([indent + tor_switch.a_name.fqdn for tor_switch in smlist]))

ObjectFormatter.handlers[SimpleTorSwitchList] = SimpleTorSwitchListFormatter()


#if __name__=='__main__':
