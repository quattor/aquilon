# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" Helper classes for notification testing """

import os
import re
from dateutil.parser import parse
from time import sleep
from datetime import datetime, timedelta

# Log format:
# 2013-07-04 10:34:39,242 [INFO] sent 1 server notifications
_timestamp_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3}) ')
_server_notify_re = re.compile(r'sent (\d+) server notifications')

NOTIFY_WAIT = 10


class VerifyNotificationsMixin(object):
    def check_notification(self, basetime, count):
        logfile = os.path.join(self.config.get("broker", "logdir"),
                               "aq_notifyd.log")
        with open(logfile, "r") as f:
            lines = f.readlines()

        # The time stamps in the logfile have millisecond granularity only, so
        # force that granularity for the base time as well
        basetime = basetime.replace(microsecond=basetime.microsecond -
                                    basetime.microsecond % 1000)

        # Check the last entry first
        lines.reverse()

        found = False
        for line in lines:
            match = _timestamp_re.search(line)
            if not match:
                continue
            timestamp = parse(match.group(1))
            timestamp = timestamp.replace(microsecond=int(match.group(2)) * 1000)

            # Ignore old entries. The list contains the last entry first, so if
            # we see an old entry, we know we don't have to look for more.
            if timestamp < basetime:
                break

            match = _server_notify_re.search(line)
            if match:
                self.failUnlessEqual(int(count), int(match.group(1)),
                                     "Expected to send %s notifications, "
                                     "sent %s" % (count, match.group(1)))
                found = True
                break

        return found

    def wait_notification(self, basetime, count):
        start = datetime.now()
        delta = timedelta(seconds=NOTIFY_WAIT)
        while datetime.now() <= start + delta:
            found = self.check_notification(basetime, count)
            if found:
                return
            sleep(0.5)
        self.fail("Notifications were not sent within %d seconds" % NOTIFY_WAIT)
