# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
from aquilon.utils import monkeypatch

from sqlalchemy.ext.declarative import declarative_base

#These extensions will be coming soon...
#from aquilon.aqdb.history.history_meta import VersionedMeta
#from aquilon.aqdb.history.audit import audit_listener_for_class

class Base(object):
    def __repr__(self):
        if hasattr(self,'name'):
            return self.__class__.__name__ + ' ' + str(self.name)
        elif hasattr(self,'type'):
            return self.__class__.__name__ + ' ' + str(self.type)
        #TODO: remove the next 2 elif cases and have service/system classes override __repr__
        elif hasattr(self,'service'):
            return self.__class__.__name__ + ' ' + str(self.service.name)
        elif hasattr(self,'system'):
            return self.__class__.__name__ + ' ' + str(self.system.name)
        else:
           return '%s instance '%(self.__class__.__name__)

    @classmethod
    def get_by(cls,k, v, session):
        return session.query(cls).filter(cls.__dict__[k] == v).all()

#Base = declarative_base(metaclass=VersionedMeta, cls=Base)
Base = declarative_base(cls=Base)

@monkeypatch(Base)
def __init__(self, **kw):
    for k in kw:
        if not hasattr(type(self), k):
            msg = "%r is an invalid argument for %s" %(k, type(self).__name__)
            raise TypeError(msg)
        setattr(self, k, kw[k])


