# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
""" Transaction formatter """
import calendar

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import Xtn


class TransactionFormatter(ObjectFormatter):
    """ Format a single transaction """
    protocol = "aqdaudit_pb2"

    def format_proto(self, xtn, skeleton=None):
        container = skeleton
        if not container:
            myproto = self.loaded_protocols[self.protocol]
            container = myproto.TransactionList()
            skeleton = container.transactions.add()

        skeleton.start_time = calendar.timegm(xtn.start_time.utctimetuple())
        skeleton.username = str(xtn.username)
        skeleton.command = str(xtn.command)
        skeleton.return_code = int(xtn.return_code)
        if xtn.end:
            skeleton.end_time = calendar.timegm(
                xtn.end.end_time.utctimetuple())
        else:
            # Need some sort of value for the protobuf (since protobufs do
            # not have a concept of null).
            skeleton.end_time = 0
        skeleton.is_readonly = int(xtn.is_readonly)

        for i in xtn.args:
            arg = skeleton.arguments.add()
            arg.name = i.name
            arg.value = i.value

        return container

ObjectFormatter.handlers[Xtn] = TransactionFormatter()


class TransactionList(list):
    """ A list of transactions (xtns) to display """
    pass


class TransactionListFormatter(ListFormatter):
    """ Format lists of audit info """
    protocol = "aqdaudit_pb2"

    def format_proto(self, stlist, skeleton=None):
        if not skeleton:
            myproto = self.loaded_protocols[self.protocol]
            skeleton = myproto.TransactionList()
        for i in stlist:
            self.redirect_proto(i, skeleton.transactions.add())
        return skeleton


ObjectFormatter.handlers[TransactionList] = TransactionListFormatter()
