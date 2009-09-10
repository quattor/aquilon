# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
""" Wrapper to simplify os retreival """

from sqlalchemy.orm import join
from sqlalchemy.sql import and_
from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import OperatingSystem, Archetype
from aquilon.server.dbwrappers.archetype import get_archetype

def get_many_os(session, osname=None, osversion=None, archetype=None,
                dbarchetype=None):
    """
        Returns a convenient query object for Operating Systems

        Used when you expect an unknown sized list of operating systems
    """
    #if archetype is None and dbarchetype is None:
    #    msg = 'No usable archetype parameter'
    #    return ArgumentError(msg)
    print "get_many_os(s, '%s', '%s', '%s', '%s')"% (osname, osversion,
                                                     archetype, dbarchetype)
    q = session.query(OperatingSystem)

    if osname:
        q = q.filter_by(name=osname)

    if osversion:
        q = q.filter_by(version=osversion)

    if archetype:
        #dbarchetype = get_archetype(session, archetype)
        q = q.join('archetype').filter_by(name=archetype)
        q = q.reset_joinpoint()

    elif dbarchetype:
        q.filter_by(archetype=dbarchetype)

    return q.all()


def get_one_os(session, osname, osversion, archetype=None, dbarchetype=None):
    """
        Find a unique OS.

        As is the common case for most dbwrappers code.
    """

    name = None
    if archetype:
        name = archetype
    if dbarchetype:
        name = dbarchetype.name

    if name is None:
        msg = 'Can not determine archetype '
        return ArgumentError(msg)

    q = session.query(OperatingSystem).select_from(
        join(OperatingSystem, Archetype)).filter(
            and_(
                OperatingSystem.name==osname,
                OperatingSystem.version==osversion,
                Archetype.name==name))

    return q.one()
