# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Contains the logic for `aq add disk`."""
import re

from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, AquilonError, InternalError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.aqdb.model import Disk, LocalDisk, NasDisk, Service, Machine
from aquilon.aqdb.model.disk import controller_types
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.processes import NASAssign


class CommandAddDisk(BrokerCommand):
    """Add a disk object (local or share) to a machine"""
    # FIXME: add "controller" and "size" once the deprecated alternatives are
    # removed
    required_parameters = ["machine", "disk"]

    REGEX_CAPACITY = re.compile("\d+:\d+$")

    def _verify_params(self, dbdisks, machine, disk, controller):
        
        if (len(dbdisks) != 0):
            raise ArgumentError("Machine %s already has a disk named %s." %
                                (machine, disk))
        if controller not in controller_types:
            raise ArgumentError("%s is not a valid controller type, use one "
                                "of: %s." % (controller,
                                             ", ".join(controller_types)))

    def _get_nasassign_obj(self, machine, dbmachine, disk, dbuser, size):
        """request an auto share assignment from Resource Pool"""
        uname = str(dbuser.name)
        if dbmachine.location.rack:
            rack = dbmachine.location.rack.name
        else:
            raise ArgumentError("Machine %s is not associated with a rack."
                                % machine)
        nasassign_obj = NASAssign(machine=machine, disk=disk,
                                  owner=uname, rack=rack, size=size)
        return nasassign_obj

    def _verify_share(self, session, share, autoshare, address):
        """get share (NAS) objects from aqdb"""        
        dbservice = Service.get_unique(session, "nas_disk_share",
                                       compel=InternalError)
        dbshare = get_service_instance(session, dbservice, share)
        if autoshare:
            if not dbshare.manager == 'resourcepool':
                raise ArgumentError('Share "%s", which was assigned by '
                                    'Resource Pool, is not correctly '
                                    'configured as a Resource Pool '
                                    'managed share in Aquilon. Please '
                                    'correct Aquilon config of the share.'
                                    % share)
        else:
            self._check_capacity(dbshare, address)
        return dbshare
                
    def _check_capacity(self, dbshare, address):
        """capacity tracking for manually managed shares (not resource pool)"""
        if dbshare.manager != 'aqd':
            raise ArgumentError("Disk '%s' is managed by %s and can only be "
                                "assigned with the 'autoshare' option." %
                                ( dbshare.name, dbshare.manager))
        if not CommandAddDisk.REGEX_CAPACITY.match(address):
            raise ArgumentError("Disk address '%s' is not valid, it must "
                                "match \d+:\d+ (e.g. 0:0)." % address)
        max_clients = dbshare.enforced_max_clients
        current_clients = len(dbshare.nas_disks)
        if max_clients is not None and current_clients >= max_clients:
            raise ArgumentError("NAS share %s is full (%s/%s)" %
                                (dbshare.name, current_clients,
                                 max_clients))

    def _flush_and_validate(self, session, dbdisk, dbmetacluster):
        """insert disk object into db"""        
        try:
            session.add(dbdisk)
            session.flush()
            if dbmetacluster:
                dbmetacluster.validate()
        except InvalidRequestError, e:
            raise ArgumentError("Could not add disk: %s" % e)

    def _write_plenary_info(self, dbmachine, logger):
        """write template files"""
        plenary_info = PlenaryMachineInfo(dbmachine, logger=logger)
        plenary_info.write()

    def render(self, session, logger, machine, disk, controller, share,
               autoshare, address, comments, dbuser, size, **kw):

        # Handle deprecated arguments
        if kw.get("type"):
            controller = kw["type"]
        if kw.get("capacity"):
            size = kw["capacity"]
        if not size or not controller:
            raise ArgumentError("Please specify both --size "
                                "and --controller.")

        dbmachine = Machine.get_unique(session, machine, compel=True)
        dbdisks = session.query(Disk).filter_by(machine=dbmachine,
                                                  device_name=disk).all()
        if dbmachine.cluster:
            dbmetacluster = dbmachine.cluster.metacluster
        else:
            dbmetacluster = None
        self._verify_params(dbdisks, machine, disk, controller)
            
        if autoshare:
            nasassign_obj = self._get_nasassign_obj(machine, dbmachine, disk, dbuser, size)
            share = nasassign_obj.create()

        try:
            if share:
                dbshare = self._verify_share(session, share, autoshare, address)
                dbdisk = NasDisk(machine=dbmachine, device_name=disk,
                                 controller_type=controller,
                                 service_instance=dbshare, capacity=size,
                                 address=address, comments=comments)
            else:
                dbdisk = LocalDisk(machine=dbmachine, device_name=disk,
                                   controller_type=controller, capacity=size,
                                   comments=comments)
            self._flush_and_validate(session, dbdisk, dbmetacluster)
            self._write_plenary_info(dbmachine, logger)
        except Exception, outer:
            if autoshare:
                try:
                    nasassign_obj.delete()
                except Exception, inner:
                    logger.warn('Error undoing autoassign. '
                                'Escalate to admin: %s' % inner)
            raise outer
        return
