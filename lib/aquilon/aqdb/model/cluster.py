# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
""" tables/classes applying to clusters """
import re
from datetime import datetime

from sqlalchemy import (Column, Integer, Boolean, String, DateTime, Sequence,
                        ForeignKey, UniqueConstraint, PrimaryKeyConstraint,
                        Index)

from sqlalchemy.orm import (object_session, relation, backref, deferred,
                            joinedload, validates)
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import (Base, Host, Location, Personality,
                                ClusterLifecycle, ServiceInstance, Branch,
                                NetworkDevice, UserPrincipal)

# List of functions allowed to be used in vmhost_capacity_function
restricted_builtins = {'None': None,
                       'dict': dict,
                       'divmod': divmod,
                       'float': float,
                       'int': int,
                       'len': len,
                       'long': long,
                       'max': max,
                       'min': min,
                       'pow': pow,
                       'round': round}


def convert_resources(resources):
    """ Convert a list of dicts to a dict of lists """
    # Turn this: [{'a': 1, 'b': 1},
    #             {'a': 2, 'b': 2}]
    #
    # Into this: {'a': [1, 2],
    #             'b': [1, 2]}
    resmap = {}
    for res in resources:
        for name, value in res.items():
            if name not in resmap:
                resmap[name] = []
            resmap[name].append(value)
    return resmap

# Cluster is a reserved word in Oracle
_TN = 'clstr'
_ETN = 'esx_cluster'
_HCM = 'host_cluster_member'
_CSB = 'cluster_service_binding'
_CSBABV = 'clstr_svc_bndg'
_CAP = 'clstr_allow_per'


def _hcm_host_creator(tuple):
    host = tuple[0]
    node_index = tuple[1]
    return HostClusterMember(host=host, node_index=node_index)


class Cluster(Base):
    """
        A group of two or more hosts for high availablility or grid
        capabilities.  Location constraint is nullable as it may or
        may not be used.
    """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)
    cluster_type = Column(AqStr(16), nullable=False)
    name = Column(AqStr(64), nullable=False)

    # Lack of cascaded deletion is intentional on personality
    personality_id = Column(Integer, ForeignKey('personality.id',
                                                name='cluster_prsnlty_fk'),
                            nullable=False)

    branch_id = Column(Integer, ForeignKey('branch.id',
                                           name='cluster_branch_fk'),
                       nullable=False)

    sandbox_author_id = Column(Integer,
                               ForeignKey('user_principal.id',
                                          name='cluster_sandbox_author_fk'),
                               nullable=True)

    location_constraint_id = Column(ForeignKey('location.id',
                                               name='cluster_location_fk'))

    max_hosts = Column(Integer, nullable=True)
    # N+M clusters are defined by setting down_hosts_threshold to M
    # Simple 2-node clusters would have down_hosts_threshold of 0
    down_hosts_threshold = Column(Integer, nullable=True)
    # And that tolerance can be relaxed even further in maintenance windows
    down_maint_threshold = Column(Integer, nullable=True)
    # Some clusters (e.g. grid) don't want fixed N+M down_hosts_threshold, but
    # use percentage goals (i.e. don't alert until 5% of the population dies)
    down_hosts_percent = Column(Boolean(name="%s_down_hosts_ck" % _TN),
                                default=False, nullable=True)
    down_maint_percent = Column(Boolean(name="%s_maint_hosts_ck" % _TN),
                                default=False, nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    status_id = Column(Integer, ForeignKey('clusterlifecycle.id',
                                           name='cluster_status_fk'),
                       nullable=False)
    comments = Column(String(255))

    status = relation(ClusterLifecycle, innerjoin=True)
    location_constraint = relation(Location, lazy=False)

    personality = relation(Personality, lazy=False, innerjoin=True)
    branch = relation(Branch, lazy=False, innerjoin=True, backref='clusters')
    sandbox_author = relation(UserPrincipal)

    hosts = association_proxy('_hosts', 'host', creator=_hcm_host_creator)

    metacluster = association_proxy('_metacluster', 'metacluster')

    __table_args__ = (UniqueConstraint(name, name='cluster_uk'),
                      Index("cluster_branch_idx", branch_id),
                      Index("cluster_prsnlty_idx", personality_id),
                      Index("cluster_location_idx", location_constraint_id))
    __mapper_args__ = {'polymorphic_on': cluster_type}

    @property
    def title(self):
        if self.personality.archetype.outputdesc is not None:
            return self.personality.archetype.outputdesc
        return self.personality.archetype.name.capitalize() + " Cluster"

    @property
    def dht_value(self):
        if not self.down_hosts_percent:
            return self.down_hosts_threshold
        return int((self.down_hosts_threshold * len(self.hosts)) / 100)

    @property
    def dmt_value(self):
        if not self.down_maint_percent:
            return self.down_maint_threshold
        return int((self.down_maint_threshold * len(self.hosts)) / 100)

    @staticmethod
    def parse_threshold(threshold):
        is_percent = False
        percent = re.search(r'(\d+)(%)?', threshold)
        thresh_value = int(percent.group(1))
        if percent.group(2):
            is_percent = True
        return (is_percent, thresh_value)

    @property
    def authored_branch(self):
        if self.sandbox_author:
            return "%s/%s" % (self.sandbox_author.name, self.branch.name)
        return str(self.branch.name)

    @property
    def personality_info(self):
        if self.cluster_type in self.personality.cluster_infos:
            return self.personality.cluster_infos[self.cluster_type]
        else:
            return None

    @property
    def required_services(self):
        return self.personality.services + self.personality.archetype.services

    @property
    def virtual_machines(self):
        mach = []
        if self.resholder:
            for res in self.resholder.resources:
                # TODO: support virtual machines inside resource groups?
                if res.resource_type == "virtual_machine":
                    mach.append(res.machine)
        return mach

    def all_objects(self):
        yield self
        for dbobj in self.hosts:
            yield dbobj

    @validates('_hosts')
    def validate_host_member(self, key, value):  # pylint: disable=W0613
        session = object_session(self)
        with session.no_autoflush:
            self.validate_membership(value.host)
        return value

    def validate_membership(self, host):
        if host.hardware_entity.location != self.location_constraint and \
                self.location_constraint not in \
                host.hardware_entity.location.parents:
            raise ArgumentError("Host location {0} is not within cluster "
                                "location {1}."
                                .format(host.hardware_entity.location,
                                        self.location_constraint))

        if host.branch != self.branch or \
                host.sandbox_author != self.sandbox_author:
            raise ArgumentError("{0} {1} {2} does not match {3:l} {4} {5}."
                                .format(host, host.branch.branch_type,
                                        host.authored_branch, self,
                                        self.branch.branch_type,
                                        self.authored_branch))

    def validate(self):
        session = object_session(self)
        q = session.query(HostClusterMember)
        q = q.filter_by(cluster=self)
        q = q.options(joinedload('host'),
                      joinedload('host.hardware_entity'))
        members = q.all()
        set_committed_value(self, '_hosts', members)

        if self.max_hosts is not None and len(self.hosts) > self.max_hosts:
            raise ArgumentError("{0} has {1} hosts bound, which exceeds the "
                                "requested limit of {2}."
                                .format(self, len(self.hosts), self.max_hosts))
        if self.metacluster:
            self.metacluster.validate()

    def format_helper(self, format_spec, instance):
        # Based on format_helper() and _get_class_label() in Base
        lowercase = False
        class_only = False
        passthrough = ""
        for letter in format_spec:
            if letter == "l":
                lowercase = True
            elif letter == "c":
                class_only = True
            else:
                passthrough += letter

        if self.cluster_type == 'meta':
            clsname = self.title + " Metacluster"
        else:
            clsname = self.title + " Cluster"

        if lowercase:
            clsname = " ".join([x if x[:-1].isupper() else x.lower()
                                for x in clsname.split()])
        if class_only:
            return clsname.__format__(passthrough)
        val = "%s %s" % (clsname, instance)
        return val.__format__(passthrough)

cluster = Cluster.__table__  # pylint: disable=C0103
cluster.info['unique_fields'] = ['name']


class ComputeCluster(Cluster):
    """
        A cluster containing computers - no special characteristics
    """
    __tablename__ = 'compute_cluster'
    __mapper_args__ = {'polymorphic_identity': 'compute'}
    _class_label = 'Compute Cluster'

    id = Column(Integer, ForeignKey('%s.id' % _TN,
                                    name='compute_cluster_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

compute_cluster = ComputeCluster.__table__  # pylint: disable=C0103
compute_cluster.info['unique_fields'] = ['name']


class StorageCluster(Cluster):
    """
        A cluster of storage devices
    """
    __tablename__ = 'storage_cluster'
    __mapper_args__ = {'polymorphic_identity': 'storage'}
    _class_label = 'Storage Cluster'

    id = Column(Integer, ForeignKey('%s.id' % _TN,
                                    name='storage_cluster_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

    def validate_membership(self, host):
        super(StorageCluster, self).validate_membership(host)
        # FIXME: this should be in the configuration, not in the code
        if host.archetype.name != "filer":
            raise ArgumentError("Only hosts with archetype 'filer' can be "
                                "added to a storage cluster. {0} is "
                                "of {1:l}.".format(host, host.archetype))

storage_cluster = StorageCluster.__table__  # pylint: disable=C0103
storage_cluster.info['unique_fields'] = ['name']


# ESX Cluster is really a Grid Cluster, but we have
# specific broker-level behaviours we need to enforce

class EsxCluster(Cluster):
    """
        Specifically for our VMware esx based clusters.
    """
    __tablename__ = _ETN
    _class_label = 'ESX Cluster'

    esx_cluster_id = Column(Integer, ForeignKey('%s.id' % _TN,
                                                name='%s_cluster_fk' % _ETN,
                                                ondelete='CASCADE'),
                            primary_key=True)

    vm_count = Column(Integer, default=16, nullable=True)
    host_count = Column(Integer, default=1, nullable=False)

    # Memory capacity override
    memory_capacity = Column(Integer, nullable=True)

    network_device_id = Column(Integer,
                               ForeignKey('network_device.hardware_entity_id',
                                          name='%s_network_device_fk' % _ETN),
                               nullable=True)

    network_device = relation(NetworkDevice, lazy=False,
                              backref=backref('esx_clusters'))

    __table_args__ = (Index("%s_network_device_idx" % _ETN, network_device_id),)
    __mapper_args__ = {'polymorphic_identity': 'esx'}

    @property
    def vm_to_host_ratio(self):
        return '%s:%s' % (self.vm_count, self.host_count)

    @property
    def max_vm_count(self):
        if self.host_count == 0:
            return 0
        effective_vmhost_count = len(self.hosts) - self.down_hosts_threshold
        if effective_vmhost_count < 0:
            return 0
        return effective_vmhost_count * self.vm_count / self.host_count

    @property
    def minimum_location(self):
        location = None
        for host in self.hosts:
            if location:
                location = location.merge(host.hardware_entity.location)
            else:
                location = host.hardware_entity.location
        return location

    @property
    def vmhost_capacity_function(self):
        """ Return the compiled VM host capacity function """
        info = self.personality_info
        if info:
            return info.compiled_vmhost_capacity_function
        else:
            return None

    @property
    def virtmachine_capacity_function(self):
        """ Return the compiled virtual machine capacity function """
        # Only identity mapping for now
        return None

    def get_total_capacity(self, down_hosts_threshold=None):
        """ Return the total capacity available for use by virtual machines """
        if down_hosts_threshold is None:
            down_hosts_threshold = self.down_hosts_threshold

        if len(self.hosts) <= down_hosts_threshold:
            if self.memory_capacity is not None:
                return {'memory': self.memory_capacity}
            return {'memory': 0}

        func = self.vmhost_capacity_function
        if self.personality_info:
            overcommit = self.personality_info.vmhost_overcommit_memory
        else:
            overcommit = 1

        # No access for anything except built-in functions
        global_vars = {'__builtins__': restricted_builtins}

        resources = []
        for host in self.hosts:
            # This is the list of variables we want to pass to the capacity
            # function
            local_vars = {'memory': host.hardware_entity.memory}
            if func:
                rec = eval(func, global_vars, local_vars)
            else:
                rec = local_vars

            # Apply the memory overcommit factor. Force the result to be
            # an integer since it looks better on display
            if 'memory' in rec:
                rec['memory'] = int(rec['memory'] * overcommit)

            resources.append(rec)

        # Convert the list of dicts to a dict of lists
        resmap = convert_resources(resources)

        # Drop the <down_hosts_threshold> largest elements from every list, and
        # sum the rest
        for name in resmap:
            reslist = sorted(resmap[name])
            if down_hosts_threshold > 0:
                reslist = reslist[:-down_hosts_threshold]
            resmap[name] = sum(reslist)

        # Process overrides
        if self.memory_capacity is not None:
            resmap['memory'] = self.memory_capacity

        return resmap

    def get_capacity_overrides(self):
        """Used by the raw formatter to flag a capacity as overridden."""
        return {'memory': self.memory_capacity}

    def get_total_usage(self):
        """ Return the amount of resources used by the virtual machines """
        func = self.virtmachine_capacity_function

        # No access for anything except built-in functions
        global_vars = {'__builtins__': restricted_builtins}

        resmap = {}
        for machine in self.virtual_machines:
            # This is the list of variables we want to pass to the capacity
            # function
            local_vars = {'memory': machine.memory}
            if func:
                res = eval(func, global_vars, local_vars)
            else:
                res = local_vars
            for name, value in res.items():
                if name not in resmap:
                    resmap[name] = value
                else:
                    resmap[name] += value
        return resmap

    def validate(self):
        super(EsxCluster, self).validate()

        # Preload resources
        resource_by_id = {}
        if self.resholder:
            from aquilon.aqdb.model import VirtualMachine, ClusterResource
            session = object_session(self)
            q = session.query(VirtualMachine)
            q = q.join(ClusterResource)
            q = q.filter_by(cluster=self)
            q = q.options([joinedload('machine'),
                           joinedload('machine.primary_name'),
                           joinedload('machine.primary_name.fqdn')])
            for res in q:
                resource_by_id[res.id] = res

        # It doesn't matter how many vmhosts we have if there are no
        # virtual machines.
        if len(self.virtual_machines) <= 0:
            return

        # For calculations, assume that down_hosts_threshold vmhosts
        # are not available from the number currently configured.
        if self.down_hosts_percent:
            adjusted_host_count = len(self.hosts) - \
                int(self.down_hosts_threshold * len(self.hosts) / 100)
            dhtstr = "%d%%" % self.down_hosts_threshold
        else:
            adjusted_host_count = len(self.hosts) - self.down_hosts_threshold
            dhtstr = "%d" % self.down_hosts_threshold

        if adjusted_host_count <= 0:
            raise ArgumentError("%s cannot support VMs with %s "
                                "vmhosts and a down_hosts_threshold of %s" %
                                (format(self), len(self.hosts), dhtstr))

        # The current ratio must be less than the requirement...
        # cur_vm / cur_host <= self.vm_count / self.host_count
        # cur_vm * self.host_count <= self.vm_count * cur_host
        # Apply a logical not to test for the error condition...
        if len(self.virtual_machines) * self.host_count > self.vm_count * adjusted_host_count:
            raise ArgumentError("%s VMs:%s hosts in %s violates "
                                "ratio %s:%s with down_hosts_threshold %s" %
                                (len(self.virtual_machines), len(self.hosts),
                                 format(self), self.vm_count, self.host_count,
                                 dhtstr))

        capacity = self.get_total_capacity()
        usage = self.get_total_usage()
        for name, value in usage.items():
            # Skip resources that are not restricted
            if name not in capacity:
                continue
            if value > capacity[name]:
                raise ArgumentError("{0} is over capacity regarding {1}: "
                                    "wanted {2}, but the limit is {3}."
                                    .format(self, name, value, capacity[name]))
        return

esx_cluster = EsxCluster.__table__  # pylint: disable=C0103
esx_cluster.info['unique_fields'] = ['name']


class HostClusterMember(Base):
    """ Association table for clusters and their member hosts """
    __tablename__ = _HCM

    cluster_id = Column(Integer, ForeignKey('%s.id' % _TN,
                                            name='hst_clstr_mmbr_clstr_fk',
                                            ondelete='CASCADE'),
                        nullable=False)

    host_id = Column(Integer, ForeignKey('host.hardware_entity_id',
                                         name='hst_clstr_mmbr_hst_fk',
                                         ondelete='CASCADE'),
                     nullable=False)

    node_index = Column(Integer, nullable=False)

    # Association Proxy and relation cascading: We need cascade=all
    # on backrefs so that deletion propagates to avoid AssertionError:
    # Dependency rule tried to blank-out primary key column on deletion
    # of the Cluster and it's links. On the contrary do not have
    # cascade='all' on the forward mapper here, else deletion of
    # clusters and their links also causes deleteion of hosts (BAD)
    cluster = relation(Cluster, lazy=False, innerjoin=True,
                       backref=backref('_hosts', cascade='all, delete-orphan'))

    # This is a one-to-one relation, so we need uselist=False on the backref
    host = relation(Host, lazy=False, innerjoin=True,
                    backref=backref('_cluster', uselist=False,
                                    cascade='all, delete-orphan'))

    __table_args__ = (PrimaryKeyConstraint(cluster_id, host_id,
                                           name="%s_pk" % _HCM),
                      UniqueConstraint(host_id,
                                       name='host_cluster_member_host_uk'),
                      UniqueConstraint(cluster_id, node_index,
                                       name='host_cluster_member_node_uk'))

hcm = HostClusterMember.__table__  # pylint: disable=C0103
hcm.info['unique_fields'] = ['cluster', 'host']

Host.cluster = association_proxy('_cluster', 'cluster')


class ClusterAllowedPersonality(Base):
    __tablename__ = _CAP

    cluster_id = Column(Integer, ForeignKey('%s.id' % _TN,
                                            name='clstr_allowed_pers_c_fk',
                                            ondelete='CASCADE'),
                        nullable=False)

    personality_id = Column(Integer, ForeignKey('personality.id',
                                                name='clstr_allowed_pers_p_fk',
                                                ondelete='CASCADE'),
                            nullable=False)

    __table_args__ = (PrimaryKeyConstraint(cluster_id, personality_id),
                      Index('%s_prsnlty_idx' % _CAP, personality_id))

Cluster.allowed_personalities = relation(Personality,
                                         secondary=ClusterAllowedPersonality.__table__)


class ClusterServiceBinding(Base):
    """
        Makes bindings of service instances to clusters
    """
    __tablename__ = _CSB
    _class_label = 'Cluster Service Binding'

    cluster_id = Column(Integer, ForeignKey('%s.id' % _TN,
                                            name='%s_cluster_fk' % _CSBABV,
                                            ondelete='CASCADE'),
                        nullable=False)

    service_instance_id = Column(Integer,
                                 ForeignKey('service_instance.id',
                                            name='%s_srv_inst_fk' % _CSBABV),
                                 nullable=False)

    __table_args__ = (PrimaryKeyConstraint(cluster_id, service_instance_id),
                      Index('%s_si_idx' % _CSBABV, service_instance_id))

Cluster.service_bindings = relation(ServiceInstance,
                                    secondary=ClusterServiceBinding.__table__,
                                    backref=backref("cluster_clients"))
