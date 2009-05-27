# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""TorSwitch formatter."""


from aquilon import const
from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import TorSwitch


class TorSwitchFormatter(ObjectFormatter):
    def format_raw(self, tor_switch, indent=""):
        details = [indent + "%s: %s" %
                (tor_switch.tor_switch_hw.model.machine_type.capitalize(),
                 tor_switch.fqdn)]
        if tor_switch.ip:
            details.append(indent + "  IP: %s" % tor_switch.ip)
        details.append(self.redirect_raw(tor_switch.tor_switch_hw.location,
                                         indent+"  "))
        details.append(self.redirect_raw(tor_switch.tor_switch_hw.model,
                                         indent + "  "))
        if tor_switch.tor_switch_hw.serial_no:
            details.append(indent + "  Serial: %s" %
                           tor_switch.tor_switch_hw.serial_no)
        for om in tor_switch.observed_macs:
            details.append(indent + "  Port %d: %s" %
                           (om.port_number, om.mac_address))
            details.append(indent + "    Created: %s Last Seen: %s" %
                           (om.creation_date, om.last_seen))
        for i in tor_switch.tor_switch_hw.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
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
        details = [tor_switch.fqdn,
                   tor_switch.tor_switch_hw.location.rack,
                   tor_switch.tor_switch_hw.location.building,
                   tor_switch.tor_switch_hw.model.vendor.name,
                   tor_switch.tor_switch_hw.model.name,
                   tor_switch.tor_switch_hw.serial_no]
        if not tor_switch.tor_switch_hw.interfaces:
            details.extend([None, None, None])
            results.append(details)
        for i in tor_switch.tor_switch_hw.interfaces:
            if not i.system:
                continue
            full = details[:]
            full.extend([i.name, i.mac, i.system.ip])
            results.append(full)
        return "\n".join([",".join([str(detail or "") for detail in result])
            for result in results])

ObjectFormatter.handlers[TorSwitch] = TorSwitchFormatter()


class SimpleTorSwitchList(list):
    pass

class SimpleTorSwitchListFormatter(ObjectFormatter):
    def format_raw(self, smlist, indent=""):
        return str("\n".join([indent + tor_switch.fqdn for tor_switch in smlist]))

ObjectFormatter.handlers[SimpleTorSwitchList] = SimpleTorSwitchListFormatter()


