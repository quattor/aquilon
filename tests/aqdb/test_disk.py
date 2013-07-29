#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2013  Contributor
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

""" tests polymorphic disks """
import inspect

from utils import load_classpath, add, commit

load_classpath()

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import Base, Disk, LocalDisk, NasDisk

from test_machine import add_machine, del_machines
from test_service import (add_service, del_service, add_service_instance,
                          del_service_instance)

from nose.tools import raises

db = DbFactory()
sess = db.Session()
Base.metadata.bind = db.engine

MACHINE_NAME = 'disk_test_machine'
MODEL = 'bl45p'
NAS_SVC = 'nas_disk_share'
SHARE_NAME = 'vmware_windows_share'
FILER_NAME = 'ddnf1.devin1.ms.com'

#cache ids of all disks created, make sure they're deleted at the end.
#don't assume that the disk table is emtpy in this test
disk_id_cache = []

def clean_up():
    del_machines(sess, MACHINE_NAME)
    disk_ids = sess.query(Disk.id).all()
    if disk_ids:
        for id in disk_ids:
            if id in disk_id_cache:
                print 'disk with id %s not deleted'% (id)
                s.query(Disk).filter_by(id=id).delete()
            commit(sess)
    del_service_instance(SHARE_NAME)
    del_service(NAS_SVC)


def setup():
    print 'set up'
    clean_up()

def teardown():
    print 'tear down'
    clean_up()

# we only need this if cascaded deletion of disks doesn't work...
#def del_disks():
#    for id in disk_id_cache:
#        disk = sess.query(Disk).filter_by(id=id).first()
#       if disk:
#           sess.delete(disk)
#    commit(sess)


def test_create_local_disk():
    """ create a local disk """
    print 'setup finished'
    machine = add_machine(sess, MACHINE_NAME, MODEL)
    assert machine, "Could not create machine in %s"% (inspect.stack()[1][3])
    print machine

    disk = LocalDisk(machine=machine, capacity=180, controller_type='scsi')
    add(sess, disk)
    commit(sess)

    assert disk, 'no disk created by %s'% (inspect.stack()[1][3])
    print disk
    disk_id_cache.append(disk.id)


def test_create_nas_disk():
    svc = add_service(sess, NAS_SVC)
    assert svc, 'no %s service created by %s' %(NAS_SVC, inspect.stack()[1][3])

    si = add_service_instance(sess, NAS_SVC, SHARE_NAME)
    assert si, 'no instance created in %s'% (inspect.stack()[1][3])

    machine = add_machine(sess, MACHINE_NAME, MODEL)
    assert machine, "Could not create machine in %s"% (inspect.stack()[1][3])
    print machine

    disk = NasDisk(machine=machine, capacity=40, controller_type='sata',
            device_name='c_drive', address='0:1:0', service_instance=si)
    add(sess, disk)
    commit(sess)

    assert disk, 'no nas disk created in %s'% (inspect.stack()[1][3])
    print disk
    disk_id_cache.append(disk.id)


if __name__ == "__main__":
    import nose
    nose.runmodule()
