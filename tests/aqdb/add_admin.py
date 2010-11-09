#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
"""Give anyone with access to read the password file the aqd_admin role."""
import sys
import logging

logging.basicConfig(levl=logging.ERROR)
log = logging.getLogger('aqdb.add_admin')

import utils
utils.load_classpath()

from aquilon.config import Config
config = Config()


from subprocess import Popen, PIPE

import argparse

from aquilon.aqdb.model import Base, UserPrincipal, Role, Realm
from aquilon.aqdb.db_factory import DbFactory


def parse_cli(*args, **kw):
    parser = argparse.ArgumentParser(
        description = 'add password readers as admins')

    parser.add_argument('-v', '--verbose',
                      action  = 'store_true',
                      dest    = 'verbose',
                      help    = 'makes metadata bind.echo = True')

    parser.add_argument('-d', '--debug',
                      action  = 'store_true',
                      dest    = 'debug',
                      help    = 'write debug info on stdout')

    return parser.parse_args()


def main(*args, **kw):
    opts = parse_cli(args, kw)

    if opts.debug:
        log.setLevel(logging.DEBUG)

    db = DbFactory(verbose=opts.verbose)
    Base.metadata.bind = db.engine

    if opts.verbose:
        db.meta.bind.echo = True

    session = db.Session()

    password_file = config.get("database", "password_file")
    p = Popen(["fs", "listacl", "-path", password_file],
              stdout=PIPE, stderr=2)
    (out, err) = p.communicate()

    groups = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Access"):
            continue
        if line.startswith("Normal"):
            continue
        if line.startswith("Negative"):
            break
        info = line.split(' ', 1)
        if len(info) < 2:
            log.debug("Bad line encountered: %s", line)
            continue
        (group, perm) = info
        if not perm.startswith("r"):
            continue
        log.debug("Found group %s", group)
        groups.append(group)

    members = set()
    for group in groups:
        p = Popen(["pts", "mem", group], stdout=PIPE, stderr=2)
        (out, err) = p.communicate()
        for line in out.splitlines():
            member = line.strip()
            if member.startswith("Members"):
                continue
            if member.startswith("Groups"):
                break
            if member:
                log.debug("Found member %s from group %s", member, group)
                members.add(member)

    aqd_admin = Role.get_unique(session, "aqd_admin", compel=True)
    realm = Realm.get_unique(session, "is1.morgan", compel=True)
    for member in members:
        q = session.query(UserPrincipal).filter_by( name=member, realm=realm)
        dbuser = q.first()
        if dbuser:
            log.info("Ensuring %s is aqd_admin", dbuser.name)
            dbuser.role = aqd_admin
        else:
            log.info("Creating %s as aqd_admin", member)
            dbuser = UserPrincipal(name=member, realm=realm, role=aqd_admin,
                                   comments='User with access to db password')
            session.add(dbuser)

    session.commit()


if __name__ == '__main__':
    main(sys.argv)
