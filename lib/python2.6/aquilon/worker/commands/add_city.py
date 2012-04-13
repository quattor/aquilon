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
"""Contains the logic for `aq add city`."""


from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.locks import lock_queue
from aquilon.worker.templates.city import PlenaryCity
from aquilon.worker.commands.add_location import CommandAddLocation


class CommandAddCity(CommandAddLocation):

    required_parameters = ["city", "timezone"]

    def render(self, session, logger, city, country, fullname, comments,
               timezone, campus,
               **arguments):

        if country:
            parentname = country
            parenttype = 'country'
        else:
            parentname = campus
            parenttype = 'campus'

        return CommandAddLocation.render(self, session, city, fullname, 'city',
                                         parentname, parenttype, comments,
                                         logger=logger, timezone=timezone,
                                         campus=campus, **arguments)

    def before_flush(self, session, new_loc, **arguments):

        if "timezone" in arguments:
            new_loc.timezone = arguments["timezone"]

    def after_flush(self, session, new_loc, **arguments):
        logger = arguments["logger"]

        city, country, fullname = (new_loc.name, new_loc.country.name,
                                   new_loc.fullname)

        plenary = PlenaryCity(new_loc, logger=logger)
        key = plenary.get_write_key()
        try:
            lock_queue.acquire(key)
            plenary.write(locked=True)

            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.add_city(city, country, fullname)

        except:
            plenary.restore_stash()
            raise
        finally:
            lock_queue.release(key)
