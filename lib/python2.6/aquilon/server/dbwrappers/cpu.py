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
"""Wrapper to make getting a cpu simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import Cpu, Vendor


# FIXME: CPU is not specified uniquely with just name!
def get_cpu(session, cpu):
    try:
        dbcpu = session.query(Cpu).filter_by(name=cpu).one()
    except InvalidRequestError, e:
        raise NotFoundException("Cpu %s not uniquely identified: %s" % (cpu, e))
    return dbcpu

def get_unique_cpu(session, name=None, vendor=None, speed=None):
    """Assumes vendor is a string and speed is an int."""
    q = session.query(Cpu)
    error = {}
    if name:
        error['name'] = name
        q = q.filter_by(name=name)
    if speed:
        error['speed'] = speed
        q = q.filter_by(speed=speed)
    if vendor:
        dbcpuvendor = Vendor.get_unique(session, vendor, compel=True)
        q = q.filter_by(vendor=dbcpuvendor)
        error['vendor'] = dbcpuvendor.name
    cpus = q.all()
    if not cpus:
        error_msg = " with %s" % error if error else ''
        raise NotFoundException("No matching CPU found%s." % error_msg)
    if len(cpus) > 1:
        raise ArgumentError("Could not uniquely identify CPU.")
    return cpus[0]
