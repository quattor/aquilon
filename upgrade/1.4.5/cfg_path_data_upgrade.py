#!/usr/bin/env python2.5
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
import os
import sys
import time
from multiprocessing import Process, Queue, cpu_count
from multiprocessing.managers import SyncManager

_HOME = os.path.expanduser('~daqscott')
_HOMELIB = os.path.join(_HOME, 'lib', 'python2.6')

#Can't do depends since no py26 IBM...
import ms.version
ms.version.addpkg('sqlalchemy', '0.5.5')
ms.version.addpkg('cx_Oracle','5.0.1-11.1.0.6')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import create_session

#we import these relative to the local path since we need a weird set of
#dependencies: we need build_item to have the transient column of cfg_path_id, etc.
from aquilon.aqdb.model import (Archetype, Host, ServiceInstance, BuildItem,
                                OperatingSystem)

from pprint import pprint

#TODO: make this run the sql script, and have another at finish?

def get_session(cstr):
    engine = create_engine(cstr)
    connection = engine.connect()
    return create_session(bind=connection, autoflush=True, autocommit=False)

def time_dec(func):
    def wrapper(*arg):
        t = time.clock()
        res = func(*arg)
        print func.func_name, time.clock()-t
        return res
    return wrapper

def get_one_os_cache(cstr):
    sess = get_session(cstr)
    os_cache = {}
    for os in sess.query(OperatingSystem):
        key = '%s/%s'% (os.name, os.version)
        os_cache[key] = os.id
    sess.close()
    del(sess)
    return os_cache

def get_si_cache(cstr):
    sess = get_session(cstr)
    si_cache = {}
    for si in sess.query(ServiceInstance):
        si_cache[si.cfg_path] = si.id
    sess.close()
    del(sess)
    return si_cache


def enqueue_hosts(cstr, host_q, limit=None):
    sess = get_session(cstr)
    qry = sess.query(Host.id)
    if limit:
        qry = qry.limit(limit)

    for row in qry.all():
        host_q.put(row[0])
    sess.close()

def work(cstr, host_q, os_cache, si_cache, commit_count=25):
    #1 commit per loop is a 5.5 minute execution time.
    #500 hosts per commit consistently yields deadlocks, so did 100
    sess = get_session(cstr)
    processed = 0

    generic_windows_os = sess.query(OperatingSystem).filter_by(
        name='windows').filter_by(version='generic').one()

    generic_aurora_os = sess.query(OperatingSystem).filter_by(
        version='generic').filter_by(name='linux').filter(
        Archetype.name == 'aurora').one()

    esx_os = sess.query(OperatingSystem).filter_by(name='esxi').one()
    pserver_os =sess.query(OperatingSystem).filter_by(name='ontap').one()

    while True:
        host_id = host_q.get()
        host = sess.query(Host).get(host_id)

        processed += 1
        #fix this for aurora + windows
        if host.build_items and (host.archetype.name == 'aquilon' or
                                 host.archetype.name =='vmhost'):
            for item in host.build_items:
                if item.service_instance_id:
                    continue #in case we've rerun the script for any reason
                if item.cfg_path.tld.type == 'os':
                    host.operating_system_id = os_cache[item.cfg_path.relative_path]
                    #sess.delete(item.cfg_path)
                elif item.cfg_path.tld.type == 'service':
                    if si_cache[str(item.cfg_path)]:
                        item.service_instance_id = si_cache[str(item.cfg_path)]
                    else:
                        print 'No service instance for %s'% (item.cfg_path)
                else:
                    print 'build item %s has no useable cfg_path'% (item.id)
        elif host.archetype.name == 'aurora':
            host.operating_system = generic_aurora_os
        elif host.archetype.name == 'windows':
            host.operating_system = generic_windows_os
        elif host.archetype.name == 'pserver':
            host.operating_system = pserver_os
        elif host.archetype.name == 'aquilon':
            if host.operating_system_id == None:
                host.operating_system_id = os_cache['linux/4.0.1-x86_64']
        else:
            print 'No useable os for host %s archetype %s' % (host.fqdn,
                                                              host.archetype.name)

        if host.archetype.name == 'vmhost':
            #just in case, the cache up above is linux only
            host.operating_system = esx_os

        if processed % commit_count == 0:
            try:
                sess.commit()
            except Exception, e:
                print e
                sess.rollback()

        if host_q.qsize() == 0:
            print 'committing at end'
            try:
                sess.commit()
            except Exception, e:
                print e
                sess.rollback()
            sess.close()
            break

class AqdbManager(SyncManager):
    """ Manages parallel processing upgrade queue """
    def __init__(self, timeout=120):
        #FIXME: fill in your connect string here
        #self._cstr = 'oracle://USER:PASSWORD@LNTO_AQUILON_NY'
        self._cstr = ''
        assert self._cstr, 'Add a database connection string in line 147'

        self.timeout = timeout
        self.NUMBER_OF_PROCESSES = cpu_count()
        if self.NUMBER_OF_PROCESSES < 4:
            self.NUMBER_OF_PROCESSES = 4
        self.host_q = Queue()

        self.si_cache = get_si_cache(self._cstr)
        self.os_cache = get_one_os_cache(self._cstr)

    def start(self):
        print "starting %d workers" % self.NUMBER_OF_PROCESSES
        self.workers = [Process(
            target=work, args=(self._cstr, self.host_q, self.os_cache,
                               self.si_cache))
                        for i in xrange(self.NUMBER_OF_PROCESSES)]
        for w in self.workers:
            w.start()

        enqueue_hosts(self._cstr, self.host_q) #, 500)

        for w in self.workers:
            w.join(self.timeout)

        for w in self.workers:
            w.terminate()

        #run post processing
        if post_processing(self._cstr, self.os_cache):
            print """
All hosts have an operating system, and all build items processed successfully.
Complete the schema migration by executing the post_os_upgrade.sql script.
"""

    def stop(self):
        self.host_q.put(None)
        for w in self.workers:
            w.join(self.timeout)
            #w.terminate()

        self.host_q.close()


def post_processing(cstr, os_cache):
    """ Perform tasks to verify data manipulation has been sucessful

        Run a one-off to repair any aquilon nodes that were missed: hosts that
        exist but have never been built lack an OS. Then check all hosts have
        an OS. If not, fail.

        If all have OS, remove all OS build_item related rows. Check the
        remaining rows to see that they all have a valid service_instance_id. If
        so, migration was sucessful.
    """
    sess = get_session(cstr)

    no_host_query = sess.query(Host).filter(Host.operating_system_id == None)

    bad_build_items_query = sess.query(BuildItem).filter(
        BuildItem.service_instance_id == None)

    no_os_hosts = no_host_query.all()

    if len(no_os_hosts) > 0:
        for host in no_os_hosts:
            if host.archetype.name == 'aquilon':
                host.operating_system_id = os_cache['linux/4.0.1-x86_64']
                sess.add(host)
        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            raise e

        no_os_hosts = no_host_query.all()

        if len(no_os_hosts) > 0:
            # Failure
            print 'The following hosts have no OS:'
            for host in no_os_hosts:
                print '%s: archetype %s personality %s' % (host.fqdn,
                                                           host.archetype.name,
                                                           host.personality.name)

            raise ValueError('Can not proceed while hosts with no OS exist')

    stmt = """ delete from build_item where cfg_path_id in
                  (select id from cfg_path where tld_id =
                  (select id from tld where type='os')) """
    sess.execute(text(stmt))
    sess.commit()
    sess.expunge_all()

    non_processed_build_items = bad_build_items_query.all()

    if len(non_processed_build_items) > 0:
        # Failure
        print 'The following build items are unprocessed:'

        if len(non_processed_build_items) < 200:
            #every host in the DB is too much for a usable scroll back buffer
            for item in non_processed_build_items:
                print '%s %s'% (item.host.fqdn, item.cfg_path)
        print '%s bad build items left' %(len(non_processed_build_items))

        raise ValueError('Can not proceed with unprocessed build_items')
    else:
        return True


if __name__ == '__main__':
    start = time.time()
    m = AqdbManager()
    m.start()
    end = time.time()

    print 'execution time: %s seconds'% (int(end-start))

    sys.exit(0)
