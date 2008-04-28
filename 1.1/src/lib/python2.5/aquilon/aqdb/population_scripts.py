#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent- tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Functions to populate the tables with racks, chassis,
    machines, and interfaces """
from __future__ import with_statement

import sys
sys.path.append('../..')
import random
import re

from shell import ipshell
from db import Session

from sqlalchemy.sql import and_

from location import *
from network import *
from hardware import *
from configuration import *
from interface import *
from service import *

s=Session()

cmnt = 'FAKE'
model  = s.query(Model).filter_by(name='hs21').one()
assert(model)

syslog = s.query(Service).filter_by(name='syslog').one()
assert(syslog)

prod   = s.query(Domain).filter_by(name='production').one()
assert(prod)

stat   = s.query(Status).filter_by(name='prod').one()
assert(stat)


def n_of(n,string):
    """ generate n strings with sequential integer appended
        useful for generating lots of rack/node names, etc """
    while n > 0:
        yield ''.join([string,str(n)])
        n-=1

def n_of_rand_hex(n):
    """generate n random hex chars """
    while n > 0:
        yield random.choice('0123456789abcdef')
        n-=1

def make_interfaces():
    """ generate e0 and e1 with random hex fields for FAKE commented
        machine that has none. There's a chance it might repeat but
        I'm not too worried about it, and wrapped in try/except anyway """

    for m in s.query(Machine).filter_by(comments=cmnt).all():
        if len(m.interfaces) == 0:
            for n in range(2):
                try:
                    pi=PhysicalInterface(
                        'e'+str(n),random_mac(),m,
                    comments=cmnt)
                    if n == 0:
                        pi.boot=True
                    s.save(pi)
                except Exception, e:
                    print e
                    s.rollback()
                    return
    try:
        s.commit()
    except Exception, e:
        print e
        s.close()
        return

def two_in_each():
    nodelist=[]

    cnt=machine.count().execute()
    if cnt.fetchall()[0][0] > 2000:
        print 'machine count > 2000, skipping creation'
        return

    model='hs21'
    for b in s.query(Building).all():
        racks = (Rack(r,'rack',fullname='rack %s'%r,
                      parent=b,comments=cmnt)
            for r in n_of(2,str(b.name)))

        for rack in racks:
            s.save(rack)
            chs = (Chassis(c,'chassis', fullname='chassis %s'%c,
                           parent=rack,comments=cmnt)
                for c in n_of(2,''.join([rack.name,'c'])))
        ###fix me: this only creates nodes in C1 and never in C2
        for ch in chs:
            s.save(ch)
            #the problem with no c2 nodes is in the next bit
            nodes = (Machine(ch,model,name=nodename,comments=cmnt)
                     for nodename in n_of(12,''.join([ch.name,'n'])))

        nodecount=0
        for node in nodes:
            try:
                s.save_or_update(node)
                nodelist.append(node)
            except Exception, e:
                print e
                s.rollback()
                sys.exit(1)

    try:
        s.commit()
    except Exception, e:
        s.rollback()
        print e
        sys.exit(1)

    print 'created %s nodes'%(len(nodelist))

    try:
        for node in nodelist:
            print node,type(node)
            h=Host(node,prod,stat,name=node.name,comments=cmnt)
            s.save(h)
    except Exception, e:
        print e
        s.rollback()


    try:
        s.commit()
    except Exception, e:
        print e
        s.close()
        sys.exit(1)

    print 'created %s hosts'%(len(nodelist))
    print 'creating interfaces for all those hosts'
    make_interfaces()
    print 'done'

def just_hosts():
    cnt=host.count().execute()
    if cnt.fetchall()[0][0] > 2000:
        print 'host count > 2000, skipping creation'
        return
    nodelist=s.query(Machine).all()

    for node in nodelist:
            print node, type(node), node.name
            h=Host(node,prod,stat,name=node.name,comments=cmnt)
            try:
                s.save(h)
            except Exception, e:
                print e
                s.rollback()
                continue
    try:
        s.commit()
    except Exception, e:
        print e
        s.close()
        sys.exit(1)

    print 'created %s hosts'%(len(nodelist))

""" To clear fake stuff:
    echo '.read utils/clear-fake.sql' | sqlite3 \
        /var/tmp/`whoami`/aquilondb/aquilon.db
"""
def random_mac():
    mac=[]
    for i in range(6):
        byte=''
        for a in n_of_rand_hex(2):
            byte=''.join([byte,a])
        mac.append(byte)
    return ':'.join(mac)

def make_host(name, machine,**kw):
    try:
        m=s.query(Machine).filter_by(name=machine.name).one()
    except Exception,e:
        print e
        return
    try:
        h=Host(m,name=name)
    except Exception, e:
        s.rollback()
        print e
        return

    assert(h)
    configure_host(h)

def npipm1():
    t = s.query(Host).filter_by(name='npipm1').first()
    if isinstance(t,Host):
        print 'npipm already created.'
        return

    np=s.query(Building).filter_by(name='np').one()

    rk = s.query(Rack).filter_by(name='np302').first()
    if not rk:
        rk=Rack('np302','rack',parent=np,
                comment='test rack from npipm1', fullname = 'rack np302')
        s.save(rk)
        s.commit()
        print 'created rack np302'
    c=s.query(Chassis).filter_by(name='np302c1').first()

    if not c:
        c=Chassis('np302c1','chassis',parent=rk,
                comment='a test for npipm1', fullname='chassis np302c1')
        s.save(c)
        s.commit()
        print 'created chassis np302c1'

    try:
        m=s.query(Machine).filter_by(name='np302c1n1').one()
    except Exception, e:
        print 'creating a machine np301c1n1'
        m=Machine(c,'hs20',node=1,comments='test npipm1 machine')
        s.save(m)

    pi=PhysicalInterface('e0','00:14:5e:86:d8:84',
                            m,comments='test npipm1-e0')
    pi2=PhysicalInterface('e1','00:14:5e:86:d8:85',
                            m,comments='test npipm1-e1')
    pi.ip='10.163.112.198'
    pi2.ip='10.163.112.229'
    s.save(pi)
    s.save(pi2)
    try:
        s.commit()
    except Exception, e:
        print e
        s.rollback()

    h=Host(m,prod,stat,name='npipm1',comments='test npipm1')
    s.save_or_update(h)

    try:
        s.commit()
    except Exception,e:
        print e
        s.rollback()
    s.flush()
    make_syslog_si('npipm1')

def get_server_for(svc,host):
    #passing it in for now, this isn't efficient in a loop
    #try:
    #    svc=s.query(Service).filter_by(name=svc_name).one()
    #    assert(svc)
    #except Exception, e:
    #    print "Can't find service named '%s' "%(svc_name)
    #    return

    """ for afs search first in the building, then in the hub
        A later extension is to add chassis, rack first """

    for loc in [host.location.building,host.location.hub]:
        sm=s.query(ServiceMap).filter_by(
                location=loc).join(
                'service_instance').filter(
                ServiceInstance.service==svc).all()
        if len(sm) > 1:
                return least_loaded(sm)
        elif len(sm) == 1:
            return sm[0]

    print 'Unable to find an appropriate service mapping'
    return False
    #TODO: create an exception and raise it, log it
def pick_random_server(sm_list):
    """ a starter function who only chooses at random for now """
    index=random.randint(0,len(sm_list) - 1)
    return sm_list[index]

def sm_iterator(sm_list,n):
    """ generator for service instances by a list of service maps.
        Useful to iterate through candidate lists of service maps """
    while n >= 0:
        yield sm_list[n]
        n-=1

def show_load():
    sm_list = s.query(ServiceMap).all()
    sml = []
    for sm in sm_iterator(sm_list,len(sm_list)-1):
        i = sm.service_instance
        sml.append((i.counter,sm))
    sml.sort()
    return sml

def least_loaded(sm_list):
    """ return the service instance with the fewest clients using it """

    candidates = []
    for sm in sm_iterator(sm_list,len(sm_list)-1):
        i = sm.service_instance
        candidates.append((i.counter,sm))
    candidates.sort()
    #print candidates
    return candidates[0][1] #if there's a tie, just return the first one

    #return the lowest...construct a dict of name, count.

def pick_servers():
    s=Session()

    try:
        svc=s.query(Service).filter_by(name='afs').one()
    except Exception, e:
        print "Can't find service named '%s' "%(svc_name)
        return
    #TODO: make this iterative over all services in the "service_list" of
    #aquilon instead of hardcoded afs.

    hlist = s.query(Host).all()
    for h in hlist:
        if len(h.templates) < 1:
            try:
                srv_map=get_server_for(svc,h)
            except Exception,e:
                print Exception,e
                continue

            if srv_map:
                #print "    picked %s for %s"%(
                    #srv_map.service_instance.system.fqdn,h.name)
                bi=BuildItem(h,srv_map.service_instance.cfg_path,3)
                try:
                    s.save(bi)
                    #s.commit()
                except Exception, e:
                    print Exception, e
                    s.rollback()
                    return False
            else:
                #print "    can't determine a cell for %s"%(h.name)
                pass
        else:
            #print '%s already has a cell: %s'%(h.name,h.templates[0])
            pass
    s.commit()


def all_cells():
    cnt=afs_cell.count().execute().fetchall()[0][0]
    if cnt > 8:
        print 'afs cell count is %s, skipping'%(str(cnt))
        return

    _cells=['a.bv', 'a.ca', 'a.cc', 'a.cs', 'a.ct', 'a.cu', 'a.dp', 'a.ec',
            'a.fb', 'a.fl', 'a.hc', 'a.hk', 'a.hl', 'a.hn', 'a.hq', 'a.ia',
            'a.id', 'a.kb', 'a.ko', 'a.ln', 'a.ls', 'a.np', 'a.ny', 'a.oy',
            'a.oz', 'a.pa', 'a.pi', 'a.sf', 'a.ti', 'a.tk', 'a.ty', 'a.yq',
            'b.hk', 'b.hn', 'b.hq', 'b.ia', 'b.ln', 'b.np', 'b.ny', 'b.oy',
            'b.oz', 'b.tk', 'c.ln', 'c.ny', 'c.oy', 'c.oz', 'c.tk', 'd.ln',
            'd.ny', 'd.oy', 'd.oz', 'e.oz', 'm.hk', 'n.hk', 'q.hk', 'q.ia',
            'q.ln', 'q.ny', 'q.ti', 'q.tk', 'u.ny', 'v.ny', 'w.hk', 'w.ln',
            'w.ny', 'w.tk', 'z.ny']


    s=Session()

    afs=s.query(Service).filter_by(name='afs').one()
    assert(afs)

    hubs={}
    for h in s.query(Hub).all():
        hubs[str(h.name)]=h

    buildings={}
    for b in s.query(Building).all():
        buildings[str(b.name)]=b

    tld=s.query(CfgTLD).filter_by(type='service').one()
    assert(tld)

    count = 0
    for cell in _cells:
        a=s.query(AfsCell).filter_by(name=cell).first()
        if a:
            print "'%s' already created"%(a)
        else:
            """ The routine to create the config directory here is a
                convenience, or a hack depending on how you see it, or
                may be just plain uneeeded. We'll see how the broker will
                handle the complex work flow required for this task
                """
            path=os.path.join('service/afs/',cell)
            client_path=os.path.join(str(configuration.const.cfg_base),
                                     path, 'client')
            if not os.path.isdir(client_path):
                try:
                    os.makedirs(client_path)
                except exceptions.OSError, e:
                    print e
                    print 'fix this later...'
            #TODO: lookup/create the config path here. use it in bi creation.

            try:
                a=AfsCell(cell, comments='afs cell %s'%(cell))
                s.save(a)
            except Exception,e:
                s.rollback()
                print e
                continue
        #make cfg_path
        si=ServiceInstance(afs,a,comments='afs')
        s.save(si)
        s.commit()

        loc_name = cell.partition('.')[2].partition('.')[0]
        if loc_name in hubs:
            sm=ServiceMap(si,hubs[loc_name], comments='afs')
            s.save(sm)
        elif loc_name in buildings:
            sm=ServiceMap(si,buildings[loc_name],comments='afs')
            s.save(sm)
            s.commit()
            count +=1
        else:
            print "FOUND NOTHING FOR '%s'"%(loc_name)

    print 'initialized %s cells with svc instances+maps'%(count)

    try:
        s.commit()
        s.flush()
    except Exception, e:
        s.close()
        print e
        return False
    print 'persisted %s afs cells to database'%(count)
    return True


def make_syslog_si(hostname):
    assert(syslog)

    h=s.query(Host).filter_by(name=hostname).one()

    si=ServiceInstance(syslog,h)
    s.save(si)
    try:
        s.commit()
    except Exception,e:
        s.rollback
        print e
        return False
    assert(si)
    print 'added %s service instances'%(syslog)
    return True

def clone_dsdb_host(hostname):
    print 'cloning %s'%(hostname)
    #need building, rack and chassis
    #need model/type, afs cell, pod

def fill_ips(ip,mask,cidr,net_id):
    s=Session()
    cidr=cidr_cache[mask]

    icn= ipcalc.Network('%s/%s'%(ip,cidr))

    for x in icn:
        is_net=False
        is_bcast=False
        used=False

        p=str(x).split('.')
        a=int(ip[0])
        b=int(ip[1])
        c=int(ip[2])
        d=int(ip[3])

        if str(x) == str(icn.network()):
            i_n=True
            used=True
        elif str(x) == str(icn.broadcast()):
            i_b=True
            used=True
        else:
            pass
        t=IpAddr( a, b, c, d, is_network=is_net, is_broadcast=is_bcast,
                 is_used=used, network_id=net_id )
        try:
            s.save(t)
        except Exception,e:
            logging.error(e)
            s.rollback()
            return
    try:
        s.commit()
    except IntegrityError,e:
        logging.error("Can't commit IPs for %s"%(ip))
        logging.error(e)
        s.rollback()
        pass
    except Exception,e:
        logging.error('In Ip Address commit for %s'%(ip))
        logging.error(Exception, e)
        s.rollback()
        pass



if __name__ == '__main__':
    two_in_each()
    just_hosts()

    npipm1()
    all_cells()
    pick_servers()
    a=show_load()
    a.reverse()
    for i in a:
        print i
    #ipshell()


###### Look into doing stuff like below:
    #for sql in _testsql: e.execute(sql) #doctest: +ELLIPSIS
"""
    delete from physical_interface where interface_id in \
        (select id from interface where comments like '%FAKE%');

    delete from interface where comments like '%FAKE%';
    delete from host where comments like '%FAKE';
    delete from machine where comments like '%FAKE%';
    delete from system where comments like '%FAKE';
    delete from rack where id in (select id from location where comments like '%FAKE%');
    delete from chassis where id in (select id from location where comments like '%FAKE%');
    delete from location where comments like '%FAKE%';
"""
