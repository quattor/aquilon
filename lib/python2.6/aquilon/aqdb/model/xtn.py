# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
    # Force the use of UTC if the underlying data type does not handle time zone
    # information correctly
    start_time = Column(UTCDateTime(timezone=True),
                        default=utcnow, nullable=False)

    end = relationship("XtnEnd", uselist=False, lazy="joined")
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
        results = []
        for arg in self.args:
            if arg.name == "__RESULT__":
                results.append(arg.value)
                continue
            elif arg.name.startswith("__RESULT__:"):
                results.append("%s=%s" % (arg.name[11:], arg.value))
                continue

            # TODO: remove the str() once we can handle Unicode
            try:
                msg.append("--%s=%r" % (arg.name, str(arg.value)))
            except UnicodeEncodeError:  # pragma: no cover
                msg.append("--%s=<Non-ASCII value>" % arg.name)
        if results:
            msg.append("[Result: " + " ".join(results) + "]")
        return " ".join(msg)


xtn = Xtn.__table__  # pylint: disable=C0103
xtn.primary_key.name = 'XTN_PK'  # pylint: disable=C0103

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


xtn_detail = XtnDetail.__table__  # pylint: disable=C0103
xtn_detail.primary_key.name = 'XTN_DTL_PK'

Xtn.args = relationship(XtnDetail, lazy="joined", order_by=[XtnDetail.name])


Index('xtn_dtl_name_idx', xtn_detail.c.name, oracle_compress=True)
Index('xtn_dtl_value_idx', xtn_detail.c.value, oracle_compress=True)

if config.has_option('database', 'audit_schema'):  # pragma: no cover
    schema = config.get('database', 'audit_schema')
    xtn.schema = schema
    xtn_end.schema = schema
    xtn_detail.schema = schema


def start_xtn(session, xtn_id, username, command, is_readonly, details,
              options_to_split=None):
    """ Wrapper to log the start of a transaction (or running command).

    Takes a dictionary with the transaction parameters.  The keys are
    command, usename, readonly, and details.  The details parameter
    is itself a a dictionary of option names to option values provided
    for the command.

    The options_to_split is a list of any options that need to be
    split on newlines.  Typically this is --list and/or --hostlist.

    """

    # TODO: (maybe) use sql inserts instead of objects to avoid added overhead?
    # We would be able to exploit executemany() for all the xtn_detail rows
    x = Xtn(xtn_id=xtn_id, command=command, username=username,
            is_readonly=is_readonly)
    session.add(x)

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

    if len(details.keys()) > 0:
        for k, v in details.iteritems():
            x = XtnDetail(xtn_id=xtn_id, name=k, value=v)
            session.add(x)
    try:
        session.commit()
    except Exception, e:  # pragma: no cover
        session.rollback()
        log.error(e)
        # Abort the command if a log entry cannot be created.
        raise


def end_xtn(session, xtn_id, return_code, results=None):
    """ Take an audit message and commit the transaction completion. """

    session.add(XtnEnd(xtn_id=xtn_id, return_code=return_code))
    if results:
        for name, value in results:
            session.add(XtnDetail(xtn_id=xtn_id, name='__RESULT__:' + str(name),
                                  value=str(value)))

    try:
        session.commit()
    except Exception, e:  # pragma: no cover
        session.rollback()
        log.error(e)
        # Swallow the error - can't do anything about this, and the
        # user really can't do anything about this.
