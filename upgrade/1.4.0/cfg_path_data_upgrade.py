#!/ms/dist/python/PROJ/core/2.6.1/bin/python
import os
import sys
import time
from multiprocessing import Process, Queue
from multiprocessing.managers import SyncManager

_HOME = os.path.expanduser('~daqscott')
_HOMELIB = os.path.join(_HOME, 'lib', 'python2.6')
_LIBDIR = os.path.join(_HOME, 'git', 'aqd', 'lib', 'python2.5')

if _LIBDIR not in sys.path:
    sys.path.insert(0, _LIBDIR)

import aquilon.aqdb.depends
from aquilon.aqdb.model import Host, ServiceInstance, OperatingSystem
from sqlalchemy import create_engine
from sqlalchemy.orm import create_session

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

def get_os_cache(cstr):
    sess = get_session(cstr)
    os_cache = {}
    for os in sess.query(OperatingSystem):
        if os.name == 'linux':
            os_cache[os.version] = os.id
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

def work(cstr, host_q, os_cache, si_cache, commit_count=50):
    #1 commit per loop is a 5.5 minute execution time.
    #500 hosts per commit consistently yields deadlocks, so did 100
    sess = get_session(cstr)
    processed = 0

    while True:
        host_id = host_q.get()
        host = sess.query(Host).get(host_id)

        processed += 1
        if host.build_items and host.archetype.name == 'aquilon':
            for item in host.build_items:
                if item.cfg_path.tld.type == 'os':
                    ver = item.cfg_path.relative_path.split('/')[1]
                    host.operating_system_id = os_cache[ver]

                elif item.cfg_path.tld.type == 'service':
                    item.service_instance_id = si_cache[str(item.cfg_path)]
                else:
                    print 'build item %s has no useable cfg_path'% (item.id)
        #TODO: else: do something for windows/aurora hosts

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
    def __init__(self, timeout=120):
        self._cstr = 'oracle://daqscott:vau849tt@LNTO_AQUILON_NY'
        self.timeout = timeout
        self.NUMBER_OF_PROCESSES = 4
        self.host_q = Queue()

        self.si_cache = get_si_cache(self._cstr)
        self.os_cache = get_os_cache(self._cstr)

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

    def stop(self):
        self.host_q.put(None)
        for w in self.workers:
            w.join(self.timeout)
            #w.terminate()

        self.host_q.close()


if __name__ == '__main__':
    m = AqdbManager()

    start = time.time()
    m.start()
    end = time.time()

    print 'execution time: %s seconds'% (int(end-start))
    sys.exit(0)


#def process_host(host):
#    for item in host.build_items:
#        if item.cfg_path.tld.type == 'os':
#
#            print '%s %s'%(host.fqdn, item.cfg_path.relative_path.split('/'))
            #object_session(self).query(Foo).filter_by(
            #host.operating_system_id = os_cache[
            #    item.cfg_path.relative_path.split('/')[1]]

            #sess.delete(item)
            #delete OS build items later in raw sql (performance)

        #if item.cfg_path.tld.type == 'service':
        #    item.service_instance_id = si_cache[str(item.cfg_path)]
            #delete the cfg_path entry in the build item row
        #    item.cfg_path=None
