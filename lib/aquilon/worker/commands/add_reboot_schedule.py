# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq add reboot schedule`."""

import re
from dateutil.parser import parse
from six import iteritems

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import RebootSchedule
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_resource import CommandAddResource


class CommandAddRebootSchedule(CommandAddResource):

    required_parameters = ["week", "day"]
    resource_class = RebootSchedule

    COMPONENTS = {
        "week": ["1", "2", "3", "4"],
        "day": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    }
    REGEXP_VALIDATION = {
        "time": re.compile(r"^(0?(\d+):0?(\d+)|None)$"),
        "week": re.compile(r'^(:?(:?'
                           + '|'.join(COMPONENTS["week"]) + ')(:?,(:?'
                           + '|'.join(COMPONENTS["week"]) + '))*|all)$'),
        # "day": re.compile(r'^(:?'
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

    def _validate_args(self, **arguments):
        """ Validate arguments used for adding a new record"""
        regexps = CommandAddRebootSchedule.REGEXP_VALIDATION
        for key, validator in iteritems(regexps):
            if key in arguments:
                data = str(arguments.get(key))
                if not validator.match(data):
                    err = "Key '%s' contains an invalid value." % key
                    if key in self.required_parameters:
                        validvals = '|'.join(self.COMPONENTS[key])
                        if key == 'week':
                            validvals += '|all'
                        err += " Valid values are (%s)." % validvals
                    raise ArgumentError(err)

                if re.search(',', data):
                    dups = dict()

                    for sub in data.split(','):
                        if sub not in self.COMPONENTS[key]:
                            raise ArgumentError("Parameter %s is not valid %s."
                                                % (sub, key))

                        if sub in dups:
                            raise ArgumentError("Parameter %s duplicated in %s."
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

    def add_resource(self, session, logger, comments, **arguments):
        arguments = self._validate_args(**arguments)

        time = arguments["time"]
        week = arguments["week"].capitalize()
        day = arguments["day"].capitalize()
        if time is not None:
            try:
                parse(time)
            except (ValueError, TypeError) as e:
                raise ArgumentError("The preferred time '%s' could not be "
                                    "interpreted: %s" % (time, e))

        res = RebootSchedule(name="reboot_schedule", time=time, week=week,
                             day=day, comments=comments)

        return res

    def render(self, **kwargs):
        return super(CommandAddRebootSchedule, self).render(metacluster=None,
                                                            **kwargs)
