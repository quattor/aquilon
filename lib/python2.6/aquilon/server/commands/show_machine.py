# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Contains the logic for `aq show machine`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.system import get_system
from aquilon.aqdb.model import Machine, Model
from aquilon.utils import force_int


class CommandShowMachine(BrokerCommand):

    def render(self, session, machine, model, vendor, machine_type, chassis,
               slot, **arguments):
        q = session.query(Machine)
        if machine:
            # TODO: This command still mixes search/show facilities.
            # For now, give an error if machine name not found, but
            # also allow the command to be used to check if the machine has
            # the requested attributes (via the standard query filters).
            # In the future, this should be clearly separated as 'show machine'
            # and 'search machine'.
            Machine.get_unique(session, machine, compel=True)
            q = q.filter_by(name=machine)
        dblocation = get_location(session, **arguments)
        if dblocation:
            q = q.filter_by(location=dblocation)
        if chassis:
            dbchassis = get_system(session, chassis)
            q = q.join('chassis_slot')
            q = q.filter_by(chassis=dbchassis)
            q = q.reset_joinpoint()
        if slot:
            slot = force_int("slot", slot)
            q = q.join('chassis_slot')
            q = q.filter_by(slot_number=slot)
            q = q.reset_joinpoint()
        if model or vendor or machine_type:
            subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                            machine_type=machine_type,
                                            compel=True)
            q = q.filter(Machine.model_id.in_(subq))
        return q.order_by(Machine.name).all()
