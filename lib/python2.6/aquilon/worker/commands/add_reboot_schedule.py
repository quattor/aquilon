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

import re

from dateutil.parser import parse

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import RebootSchedule
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)


class CommandAddRebootSchedule(BrokerCommand):

    required_parameters = ["week", "day"]

    COMPONENTS = {
        "week": ["1", "2", "3", "4", "5"],
        "day": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    }
    REGEXP_VALIDATION = {
        "time": re.compile(r"^(:?[0-9:]+|None)$"),
        "week": re.compile(r'^(:?(:?'
                           + '|'.join(COMPONENTS["week"]) + ')(:?,(:?'
                           + '|'.join(COMPONENTS["week"]) + '))*|all)$'),
        #"day": re.compile(r'^(:?'
        #                   + '|'.join(COMPONENTS["day"]) + ')(:?,(:?'
        #                   + '|'.join(COMPONENTS["day"]) + '))*$')
        "day": re.compile(r'^(:?'
                          + '|'.join(COMPONENTS["day"])
                          + ')$')
    }

    def _fix_parameter_order(self, key, value):
        items = value.split(",")
        new = []
        for item in self.COMPONENTS[key]:
            if item in items:
                new.append(item)

        return ",".join(new)

    def _validate_args(self, logger, **arguments):
        """ Validate arguments used for adding a new record"""
        regexps = CommandAddRebootSchedule.REGEXP_VALIDATION
        for key, validator in regexps.iteritems():
            if key in arguments:
                data = str(arguments.get(key))
                if not validator.match(data):
                    raise ArgumentError("key %s contains a bad value" % key)

                if re.search(',', data):
                    dups = dict()

                    for sub in data.split(','):
                        if sub not in self.COMPONENTS[key]:
                            raise ArgumentError("parameter %s is not valid %s"
                                                % (sub, key))

                        if sub in dups:
                            raise ArgumentError("parameter %s duplicated in %s"
                                                % (sub, key))

                        dups[sub] = 1

        # enforce order to comma separated values
        if "day" in arguments:
            arguments["day"] = self._fix_parameter_order("day",
                                                         arguments["day"])

        if "week" in arguments and arguments["week"] != "all":
            arguments["week"] = self._fix_parameter_order("week",
                                                          arguments["week"])

        if "week" in arguments and arguments["week"] == "1,2,3,4,5":
            arguments["week"] = "all"

        return arguments

    def render(self, session, logger, **arguments):

        reboot_schedule = "reboot_schedule"
        validate_basic("reboot_schedule", reboot_schedule)
        arguments = self._validate_args(logger, **arguments)

        time = arguments["time"]
        week = arguments["week"].capitalize()
        day = arguments["day"].capitalize()
        hostname = arguments["hostname"]
        cluster = arguments["cluster"]
        comments = arguments["comments"]
        if time is not None:
            try:
                parse(time)
            except ValueError, e:
                raise ArgumentError("the preferred time '%s' could not be "
                                    "interpreted: %s" % (time, e))
        holder = get_resource_holder(session, hostname, cluster, compel=False)

        RebootSchedule.get_unique(session, name=reboot_schedule, holder=holder,
                                  preclude=True)

        res = RebootSchedule(name=reboot_schedule,
                             time=time,
                             week=week,
                             day=day,
                             comments=comments)

        return add_resource(session, logger, holder, res)
