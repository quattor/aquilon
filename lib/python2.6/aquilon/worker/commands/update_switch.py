# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq update switch`."""


from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.aqdb.model import Model, Switch
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.hardware_entity import (update_primary_ip,
                                                       rename_hardware)
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates.base import Plenary


class CommandUpdateSwitch(BrokerCommand):

    required_parameters = ["switch"]

    def render(self, session, logger, switch, model, rack, type, ip,
               vendor, serial, comments, rename_to, **arguments):
        dbswitch = Switch.get_unique(session, switch, compel=True)

        oldinfo = DSDBRunner.snapshot_hw(dbswitch)

        if vendor and not model:
            model = dbswitch.model.name
        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       machine_type='switch', compel=True)
            dbswitch.model = dbmodel

        dblocation = get_location(session, rack=rack)
        if dblocation:
            dbswitch.location = dblocation

        if serial is not None:
            dbswitch.serial_no = serial

        # FIXME: What do the error messages for an invalid enum (switch_type)
        # look like?
        if type:
            dbswitch.switch_type = type

        if ip:
            update_primary_ip(session, dbswitch, ip)

        if comments is not None:
            dbswitch.comments = comments

        remove_plenary = None
        if rename_to:
            # Handling alias renaming would not be difficult in AQDB, but the
            # DSDB synchronization would be painful, so don't do that for now.
            # In theory we should check all configured IP addresses for aliases,
            # but this is the most common case
            if dbswitch.primary_name and dbswitch.primary_name.fqdn.aliases:
                raise ArgumentError("The switch has aliases and it cannot be "
                                    "renamed. Please remove all aliases first.")
            remove_plenary = Plenary.get_plenary(dbswitch, logger=logger)
            rename_hardware(session, dbswitch, rename_to)

        session.flush()

        switch_plenary = Plenary.get_plenary(dbswitch, logger=logger)

        key = switch_plenary.get_write_key()
        if remove_plenary:
            key = CompileKey.merge([key, remove_plenary.get_remove_key()])
        try:
            lock_queue.acquire(key)
            if remove_plenary:
                remove_plenary.stash()
                remove_plenary.remove(locked=True)
            switch_plenary.write(locked=True)

            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.update_host(dbswitch, oldinfo)
            except AquilonError, err:
                raise ArgumentError("Could not update switch in DSDB: %s" % err)
            return
        except:
            if remove_plenary:
                remove_plenary.restore_stash()
            switch_plenary.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
