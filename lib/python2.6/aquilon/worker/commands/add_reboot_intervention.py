# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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

from dateutil.parser import parse
from datetime import datetime

from aquilon.exceptions_ import ArgumentError
from sqlalchemy.orm.exc import NoResultFound

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)
from aquilon.aqdb.model import RebootIntervention
from aquilon.aqdb.model import RebootSchedule


class CommandAddRebootIntervention(BrokerCommand):

    required_parameters = ["expiry", "justification"]

    def render(self, session, logger, expiry, start_time,
               comments, justification, hostname, cluster,
               **arguments):

        allowusers = None
        allowgroups = None
        disabled_actions = None

        # Name for the plenary and show_host output
        intervention = 'reboot_intervention'

        try:
            expire_when = parse(expiry)
        except ValueError, e:
            raise ArgumentError("the expiry value '%s' could not be "
                                "interpreted: %s" % (expiry, e))

        if start_time is None:
            start_when = datetime.utcnow().replace(microsecond=0)
        else:
            try:
                start_when = parse(start_time)

            except ValueError, e:
                raise ArgumentError("the start time '%s' could not be "
                                    "interpreted: %s" % (start_time, e))

        if start_when > expire_when:
            raise ArgumentError("the start time is later than the expiry time")

        # Check there is a reboot_schedule
        q = session.query(RebootSchedule)
        try:
            who = get_resource_holder(session, hostname, cluster)
            q.filter_by(holder=who).one()
        except NoResultFound, e:
            raise ArgumentError("there is no reboot_schedule defined")

        # More thorough check reboot_schedule and intervention
        # XXX TODO
        # i) detect week of month of start of intervention
        # ii) detect time
        # iii) compute week of application of reboot_schedule
        # iv) ... and time
        # v) test all the above doesn't conflict within 1hr of each other.

        # Setup intervention
        holder = get_resource_holder(session, hostname, cluster, compel=False)

        RebootIntervention.get_unique(session, name=intervention,
                                      holder=holder, preclude=True)

        dbiv = RebootIntervention(name=intervention,
                                  expiry_date=expire_when,
                                  start_date=start_when,
                                  users=allowusers,
                                  groups=allowgroups,
                                  disabled=disabled_actions,
                                  comments=comments,
                                  justification=justification)

        return add_resource(session, logger, holder, dbiv)
