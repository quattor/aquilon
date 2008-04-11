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

from shell import ipshell
from db import meta, engine, Session

from sqlalchemy.sql import and_

from location import *
from network import *
from service import *
from configuration import *
from hardware import *
from interface import *

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

    for b in s.query(Building).all():
        racks = (Rack(r,'rack',fullname='rack %s'%r,
                      parent=b,comments=cmnt)
            for r in n_of(2,str(b.name)))

        for rack in racks:
            s.save(rack)
            chs = (Chassis(c,'chassis', fullname='chassis %s'%c,
                           parent=rack,comments=cmnt)
                for c in n_of(2,''.join([rack.name,'c'])))

        for ch in chs:
            s.save(ch)
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
            h=Host(node,prod,stat,name=node.name,comments=cmnt)
            s.save(h)
    except Exception, e:
        print e
        s.close()
        sys.exit(1)

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
        print 'machine count > 2000, skipping creation'
        return
    nodelist=s.query(Machine).all()
    try:
        for node in nodelist:
            h=Host(node,prod,stat,name=node.name,comments=cmnt)
            s.save(h)
    except Exception, e:
        print e
        s.close()
        sys.exit(1)

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
    for i in range(4):
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

def get_server_for(svc_name,hname):
    #a=s.query(Archetype).filter_by(name='aquilon').one()
    try:
        svc=s.query(Service).filter_by(name=svc_name).one()
        assert(svc)
    except NoSuchRowException:
        print "Can't find service named '%s' "%(svc_name)
        return
    try:
        host=s.query(Host).filter_by(name=hname).one()
        assert(host)
    except NoSuchRowException:
        print "Can't find service named '%s' "%(svc_name)
        return


    """for afs search first in the building, then in the hub """
    for loc in [host.location.building,host.location.hub]:
        print 'searching for %s in %s %s...'%(svc,loc.type,loc)
        si=s.query(ServiceMap).filter_by(
                location=loc).join(
                'service_instance').filter(
                ServiceInstance.service==svc).all()
        if len(si) > 1:
                print 'found %s service maps'%(len(si))
                print si
        elif len(si) == 1:
            print 'found it: %s'%si[0]
            return si[0]
        else:
            print 'no afs in %s %s\n\n'%(loc.type,loc)

    return

def all_cells():
    cnt=afs_cell.count().execute().fetchall()[0][0]
    if cnt > 8:
        print 'afs cell count is %s, skipping'%(str(cnt))
        return

    afs=s.query(Service).filter_by(name='afs').one()
    assert(afs)

    hubs={}
    for h in s.query(Hub).all():
        hubs[str(h.name)]=h

    buildings={}
    for b in s.query(Building).all():
        buildings[str(b.name)]=b

    count = 0
    with open('../../../../etc/data/afs_cells') as f:
        for line in f.readlines():
            if line.isspace():
                continue
            line = line.strip()

            a=s.query(AfsCell).filter_by(name=line).first()
            if a:
                print "'%s' already created"%(a)
            else:
                try:
                    a=AfsCell(line,'afs_cell', comments='afs cell %s'%(line))
                    s.save(a)
                except Exception,e:
                    s.rollback()
                    print e
                    continue

            si=ServiceInstance(afs,a)
            s.save(si)

            loc_name = line.partition('.')[2].partition('.')[0]
            if loc_name in hubs:
                print 'Creating hub level service map at %s for %s'%(
                    loc_name,line)
                sm=ServiceMap(si,hubs[loc_name])
                s.save(sm)
            elif loc_name in buildings:
                print 'Creating building level svc map %s for %s '%(
                    loc_name,line)
                sm=ServiceMap(si,buildings[loc_name])
                s.save(sm)
                count +=1
            else:
                print "FOUND NOTHING FOR '%s'"%(loc_name)

    print 'initialized %s cells with svc instances+maps'%(count)

    try:
        s.commit()
    except Exception, e:
        s.close()
        print e
        return False
    print 'persisted %s afs cells to database'%(count)
    print s.query(AfsCell).all()
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
    print 'added %s service instances'%(syslog)
    return True

def clone_dsdb_host(hostname):
    print 'cloning %s'%(hostname)
    #need building, rack and chassis
    #need model/type, afs cell, pod

def npipm1():
    t = s.query(Host).filter_by(name='npipm1').first()
    if isinstance(t,Host):
        print 'npipm already created.'
        return

    np=s.query(Building).filter_by(name='np').one()
    mod=s.query(Model).filter_by(name='ls20').one()

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
        m=s.query(Machine).filter_by(name='npipm1').one()
    except Exception, e:
        print 'creating a machine npipm1'
        m=Machine(c,mod,node=1,comments='test npipm1 machine')
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



#############

if __name__ == '__main__':
    two_in_each()
    just_hosts()

    npipm1()
    all_cells()
    get_server_for('afs','aj1c1n6')
    #ipshell()

"""
def np_racks():
    print 'populating all racks in building NP'
    s=Session()

    b=s.query(Building).filter_by(name='np').one()
    with open('../../../../etc/data/np-racks','r') as f:
        for line in f.readlines():
            name=line
            r=Rack(name,'rack',parent=b,fullname='rack %s'%(name))
            s.save(r)
        s.flush()

def np_chassis():
    print 'populating all chassis in building NP'
    s=Session()
    b=s.query(Building).filter_by(name='np').one()
    with open('../../../../etc/data/np-chassis','r') as f:
        for line in f.readlines():
            n=line.strip()
            (rack,c,num) = line.partition('c')
            c=Chassis(n,'chassis',fullname='chassis %s'%(n),parent=s.query(
                Rack).filter_by(name=rack).one())
            s.save(c)
        s.commit()

def populate_np_nodes():
    cnt=machine.count().execute()
    if cnt.fetchall()[0][0] < 2:
        s=Session
        mod=Session.query(Model).filter_by(name='hs20').one()
        with open('../../../../etc/data/np-nodes','r') as f:
            for line in f.readlines():
                (c,q,num)=line.strip().lstrip('n').partition('n')
                c='n'+c
                try:
                    r=s.query(Chassis).filter_by(name=c).one()
                except Exception,e:
                    print 'no such chassis %s'%c
                    continue
                m=Machine(r,mod,name=line.strip())
                s.save(m)
        s.commit()
        s.close()
"""
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
