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
""" handy for comparing networks """


from ipaddr import IPv4Network

from aquilon.aqdb.model import Network


class NetRecord(object):
    """ To make comparing dsdb and aqdb network structures easier """

    def __init__(self, *args, **kw):
        #TODO: update comments later, it's too much noise for now
        # Only need/want dsdb bldg in case location is unmatched.
        # Even there bldg is occasionally null, so mark it optional.
        _required = ['name', 'ip', 'cidr', 'side', 'net_type']
        _optional = ['bldg', 'location']
        for (k, v) in kw.iteritems():
            setattr(self, k, v)

        #default to side 'a'
        if not getattr(self, 'side', None):
            self.side = 'a'

        for r in _required:
            if not getattr(self, r, None):
                msg="no required '%s' attr."%(r)
                raise ValueError(msg)
        for o in _optional:
            setattr(self, o, getattr(self, o, None))

    def __eq__(self, other):
        # This is a really ugly override of __eq__.  Maybe something like
        # matches() would have been a more appropriate name.
        if self.ip != other.ip:
            msg = 'subnet IP mismatch (dsdb)%s != %s(aqdb)'%(self.ip, other.ip)
            raise ValueError(msg)

        if type(other) != Network:
            msg = 'type of %s is %s, should be Network'%(other,type(other))
            raise TypeError(msg)

        if (self.name.strip().lower() == other.name and
            self.net_type == other.network_type and
            self.cidr == other.cidr and
            self.location == other.location and
            self.side == other.side): #and
            #self.comments == other.comments):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def update_aq_net(self, dbnetwork, nr):
        if type(dbnetwork) != Network:
            # The uncaught TypeError would translate up as an InternalError,
            # which seems like the right behavior.
            raise TypeError('update_aq_net %s is %s, should be Network' %
                            (dbnetwork, type(dbnetwork)))
        if self.ip != dbnetwork.ip:
            m = 'update_aq_net: network ip mismatch (dsdb)%s != %s(aqdb)' % (
                self.ip, dbnetwork.ip)
            raise ValueError(m)

        if self.location != dbnetwork.location:
            nr.info('updating network %s to %s %s',
                    dbnetwork, self.location.location_type, self.location.name)
            dbnetwork.location = self.location

        if self.name.strip().lower() != dbnetwork.name:
            nr.info('updating network %s to name %s', dbnetwork, self.name)
            dbnetwork.name = self.name

        if self.net_type != dbnetwork.network_type:
            nr.info('updating network %s to type %s', dbnetwork, self.net_type)
            dbnetwork.network_type = self.net_type

        if self.cidr != dbnetwork.cidr:
            net = IPv4Network("%s/%s" % (str(dbnetwork.ip), self.cidr))
            nr.info('updating network %s with %s', dbnetwork, net)
            dbnetwork.network = net

        if self.side != dbnetwork.side:
            nr.info('updating network %s to side %s', dbnetwork, self.side)
            dbnetwork.side = self.side

        return dbnetwork

    def __repr__(self):
        return '<Network %s ip=%s, type=%s, cidr=%s, bldg=%s, side=%s>' % (
            self.name, self.ip, self.net_type, self.cidr, self.bldg, self.side)
