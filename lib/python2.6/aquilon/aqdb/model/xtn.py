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
""" Xtn (transaction) is an audit trail of all broker activity """
import logging
from datetime import datetime
from dateutil.tz import tzutc

from sqlalchemy import Column, String, Integer, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship, backref

from aquilon.config import Config
from aquilon.aqdb.model.base import Base
from aquilon.aqdb.column_types import GUID, UTCDateTime

config = Config()
log = logging.getLogger('aquilon.aqdb.model.xtn')


def utcnow(context, tz=tzutc()):
    return datetime.now(tz)


class Xtn(Base):
    """ auditing information from command invocations """
    __tablename__ = 'xtn'
    __table_args__ = {'oracle_compress': True}

    xtn_id = Column(GUID(), primary_key=True)
    username = Column(String(65), nullable=False, default='nobody')
    command = Column(String(64), nullable=False)
    # This column is *massively* redundant, but we're fully denormalized
    is_readonly = Column(Boolean(name="XTN_IS_READONLY"), nullable=False)
    # Note this column is forced to be UTC by the column type. The timezone is
    # not explicitly stored as data in the table
    start_time = Column(UTCDateTime(timezone=True),
                        default=utcnow, nullable=False)

    args = relationship("XtnDetail", backref=backref("xtn"), lazy="joined")

    end = relationship("XtnEnd", uselist=False, backref=backref("xtn_start"),
                       lazy="joined")
    # N.B. NO "cascade". Transaction logs are *never* deleted/changed
    # Given that, we don't really *need* the foreign key, but we'll keep it
    # unless it proves otherwise cumbersome for performance (mainly insert).

    @property
    def return_code(self):
        """ List the return code as 0 for commands that are not completed."""
        if self.end:
            return self.end.return_code
        else:
            return 0

    def __str__(self):
        if self.end:
            return_code = self.end.return_code
        else:
            return_code = '-'

        msg = [self.start_time.strftime('%Y-%m-%d %H:%M:%S%z'),
               str(self.username), str(return_code), 'aq', str(self.command)]
        for arg in self.args:
            # TODO: remove the str() once we can handle Unicode
            try:
                msg.append("--%s=%r" % (arg.name, str(arg.value)))
            except UnicodeEncodeError:  # pragma: no cover
                msg.append("--%s=<Non-ASCII value>" % arg.name)
        return " ".join(msg)


xtn = Xtn.__table__  # pylint: disable=C0103, E1101
xtn.primary_key.name = 'XTN_PK'  # pylint: disable=C0103, E1101

Index('XTN_USERNAME_IDX', xtn.c.username, oracle_compress=True)
Index('XTN_COMMAND_IDX', xtn.c.command, oracle_compress=True)
Index('XTN_ISREADONLY_IDX', xtn.c.is_readonly, oracle_bitmap=True)
Index('XTN_START_TIME_IDX', xtn.c.start_time, oracle_desc=True)


class XtnEnd(Base):
    """ A record of a completed command/transaction """
    __tablename__ = 'xtn_end'
    __table_args__ = {'oracle_compress': True}

    xtn_id = Column(GUID(),
                    ForeignKey(Xtn.xtn_id, name='XTN_END_XTN_FK'),
                    primary_key=True)
    return_code = Column(Integer, nullable=False)
    end_time = Column(UTCDateTime(timezone=True),
                      default=utcnow, nullable=False)

xtn_end = XtnEnd.__table__
xtn_end.primary_key.name = 'XTN_END_PK'
Index('XTN_END_RETURN_CODE_IDX', xtn_end.c.return_code, oracle_compress=True)


class XtnDetail(Base):
    """ Key/Value argument pairs for executed commands """
    __tablename__ = 'xtn_detail'
    __table_args__ = {'oracle_compress': True}

    xtn_id = Column(GUID(),
                    ForeignKey(Xtn.xtn_id, name='XTN_DTL_XTN_FK'),
                    primary_key=True)

    name = Column(String(255), primary_key=True)
    value = Column(String(255), default='True', primary_key=True)


xtn_detail = XtnDetail.__table__  # pylint: disable=C0103, E1101
xtn_detail.primary_key.name = 'XTN_DTL_PK'

Index('xtn_dtl_name_idx', xtn_detail.c.name, oracle_compress=True)
Index('xtn_dtl_value_idx', xtn_detail.c.value, oracle_compress=True)

if config.has_option('database', 'audit_schema'):  # pragma: no cover
    schema = config.get('database', 'audit_schema')
    xtn.schema = schema
    xtn_end.schema = schema
    xtn_detail.schema = schema


def start_xtn(session, record, options_to_split=None):
    """ Wrapper to log the start of a transaction (or running command).

    Takes a dictionary with the transaction parameters.  The keys are
    command, usename, readonly, and details.  The details parameter
    is itself a a dictionary of option names to option values provided
    for the command.

    The options_to_split is a list of any options that need to be
    split on newlines.  Typically this is --list and/or --hostlist.

    """

    log.debug('start_xtn: recieved %s', record)
    xtn_id = record.pop('xtn_id')

    # TODO: (maybe) use sql inserts instead of objects to avoid added overhead?
    # We would be able to exploit executemany() for all the xtn_detail rows
    x = Xtn(xtn_id=xtn_id,
            command=record.pop('command'),
            username=record.pop('username'),
            is_readonly=record.pop('readonly'))
    session.add(x)
    # Force a commit here to work around behavior in sqlalchemy 0.6.
    # Should be fixed in 0.7.0:
    # http://www.sqlalchemy.org/trac/ticket/2082
    # http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg23124.html
    try:
        session.commit()
    except Exception, e:  # pragma: no cover
        session.rollback()
        log.error(e)
        # Abort the command if a log entry cannot be created.
        raise

    log.debug('start_xtn: %s committed', x)

    # Only thing left in the record are the details...
    details = record.pop('details', dict())

    if options_to_split:
        for option in options_to_split:
            list_args = details.pop(option, None)
            if not list_args:
                continue
            for item in list_args.strip().split('\n'):
                item = item.strip()
                if not item:
                    continue
                x = XtnDetail(xtn_id=xtn_id, name=option, value=item)
                session.add(x)

    log.debug("start_xtn: finished list processing")

    if len(details.keys()) > 0:
        for k, v in details.iteritems():
            log.debug("start_xtn: '%s' = '%s'", k, v)
            x = XtnDetail(xtn_id=xtn_id, name=k, value=v)
            session.add(x)
    try:
        session.commit()
    except Exception, e:  # pragma: no cover
        session.rollback()
        log.error(e)
        # Abort the command if a log entry cannot be created.
        raise


def end_xtn(session, record):
    """ Take an audit message and commit the transaction completion. """

    log.debug("completing transaction %s", record)
    end = XtnEnd(xtn_id=record['xtn_id'],
                 return_code=record['return_code'])

    session.add(end)
    try:
        session.commit()
    except Exception, e:  # pragma: no cover
        session.rollback()
        log.error(e)
        # Swallow the error - can't do anything about this, and the
        # user really can't do anything about this.
