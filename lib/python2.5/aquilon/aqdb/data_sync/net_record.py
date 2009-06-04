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
""" handy for comparing networks """
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))

#TODO: rename _mask_to_cidr, it's not really hidden
from aquilon.aqdb.model import Network
from aquilon.aqdb.model.network import get_bcast, _mask_to_cidr


class NetRecord(object):
    """ To make comparing dsdb and aqdb network structures easier """

    def __init__(self, *args, **kw):
        #TODO: update comments later, it's too much noise for now
        _required = ['name', 'ip', 'mask', 'bldg', 'side', 'net_type']
        for k,v in kw.iteritems():
            setattr(self,k, v)

        #default to side 'a'
        if not getattr(self, 'side', None):
            self.side = 'a'

        for r in _required:
            if not getattr(self, r, None):
                msg="no required '%s' attr."%(r)
                raise ValueError(msg)

    def __eq__(self, other):
        if self.ip != other.ip:
            msg = 'subnet IP mismatch (dsdb)%s != %s(aqdb)'%(self.ip, other.ip)
            raise ValueError(msg)

        if type(other) != Network:
            msg = 'type of %s is %s, should be Network'%(other,type(other))
            raise TypeError(msg)

        if (self.name.lower() == other.name and
            self.net_type     == other.network_type and
            self.mask         == other.mask and
            self.bldg         == other.location.name and
            self.side         == other.side): #and
            #self.comments == other.comments):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def update_aq_net(self, aq, log, report):
        if type(aq) != Network:
            #TODO: make sure you're caught
            raise TypeError(
                         'diff_aq_net%s is %s, should be Network'%(aq,type(aq)))
        if self.ip != aq.ip:
            m = 'update_aq_net: network ip mismatch (dsdb)%s != %s(aqdb)'%(
                                                                self.ip, aq.ip)
            raise ValueError(m)

        if self.bldg != aq.location.name:
            m = 'update_aq_net: location name mismatch (dsdb)%s != %s(aqdb)'%s(
                                                    self.bldg, aq.location.name)
            raise ValueError(m)
        msg = ''
        if self.bldg != aq.location.name:
            msg += 'updating network %s to name %s\n'%(aq, self.name)
            report.upds.append(msg)
            log.debug(msg)

        if self.name.lower() != aq.name:
            msg += 'updating network %s to name %s'%(aq, self.name)
            log.debug(msg)
            report.upds.append(msg)
            aq.name = self.name

        if self.net_type != aq.network_type:
            msg = 'updating network %s to type %s'%(aq, self.net_type)
            log.debug(msg)
            report.upds.append(msg)
            aq.network_type = self.net_type

        if self.mask != aq.mask:
            #calculate new cidr and new bcast
            aq.mask = self.mask
            aq.cidr = _mask_to_cidr[aq.mask]
            aq.bcast = get_bcast(aq.ip, aq.cidr)

            msg = 'updating network %s with mask %s, cidr %s, bcast %s'%(
                aq, self.mask, aq.cidr, aq.bcast)

            log.debug(msg)
            report.upds.append(msg)

        if self.side != aq.side:
            msg = 'updating network %s to name %s'%(aq, self.name)
            log.debug(msg)
            report.upds.append(msg)
            aq.side = self.side

        return aq

    def __repr__(self):
        return '<Network %s ip=%s, type=%s, mask=%s, bldg=%s, side=%s>'%(
                self.name, self.ip, self.net_type, self.mask,
                self.bldg, self.side)


