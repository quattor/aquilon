# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
"""Wrappers to make getting and using systems simpler."""


from aquilon.exceptions_ import (IncompleteError, NotFoundException,
                                 ArgumentError)
from aquilon.aqdb.model import (Cluster, ClusterResource, HostResource,
                                Resource, ResourceGroup, BundleResource)
from aquilon.worker.templates import Plenary
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.locks import lock_queue, CompileKey


def get_resource_holder(session, hostname=None, cluster=None, resgroup=None,
                        compel=True):
    who = None
    if hostname is not None:
        dbhost = hostname_to_host(session, hostname)
        who = dbhost.resholder
        if who is None:
            if compel:
                raise NotFoundException("{0} has no resources.".format(dbhost))
            dbhost.resholder = HostResource(host=dbhost)
            session.add(dbhost.resholder)
            session.flush()
            who = dbhost.resholder

    if cluster is not None:
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        who = dbcluster.resholder
        if who is None:
            if compel:
                raise NotFoundException("{0} has no resources.".format(dbcluster))
            dbcluster.resholder = ClusterResource(cluster=dbcluster)
            session.add(dbcluster.resholder)
            session.flush()
            who = dbcluster.resholder

    if resgroup is not None:
        dbrg = ResourceGroup.get_unique(session, name=resgroup, holder=who,
                                        compel=True)
        who = dbrg.resholder
        if who is None:
            if compel:
                raise NotFoundException("{0} has no resources.".format(dbrg))
            dbrg.resholder = BundleResource(resourcegroup=dbrg)
            session.add(dbrg.resholder)
            session.flush()
            who = dbrg.resholder

    return who


def get_resource(session, holder, **arguments_in):
    # Filter out arguments that are not resources
    arguments = dict()
    for key, value in arguments_in.items():
        if key in Resource.__mapper__.polymorphic_map and value is not None:
            arguments[key] = value
        elif key == "reboot_intervention" and value is not None:
            # Sigh... Abbreviations are bad.
            arguments["reboot_iv"] = value

    # Resource groups are act both as resource and as holder. If there's another
    # resource type specified, then use it as a holder; if it is specified
    # alone, then use it as a resource.
    if "resourcegroup" in arguments and len(arguments) > 1:
        rg_name = arguments.pop("resourcegroup")
        if not holder.resholder:
            raise NotFoundException("{0} has no resources.".format(holder))
        dbrg = ResourceGroup.get_unique(session, name=rg_name,
                                        holder=holder.resholder, compel=True)
        holder = dbrg

    if arguments:
        if len(arguments) > 1:
            raise ArgumentError("Only one resource type should be specified.")

        if not holder.resholder:
            raise NotFoundException("{0} has no resources.".format(holder))

        res_type, res_name = arguments.popitem()
        cls = Resource.__mapper__.polymorphic_map[res_type].class_
        return cls.get_unique(session, name=res_name, holder=holder.resholder,
                              compel=True)
    return None


def del_resource(session, logger, dbresource, dsdb_callback=None, **arguments):
    holder = dbresource.holder
    holder_plenary = Plenary.get_plenary(holder.holder_object, logger=logger)
    remove_plenary = Plenary.get_plenary(dbresource)

    domain = holder.holder_object.branch.name

    holder.resources.remove(dbresource)
    session.flush()

    key = CompileKey.merge([remove_plenary.get_remove_key(),
                            holder_plenary.get_write_key()])
    try:
        lock_queue.acquire(key)
        remove_plenary.stash()
        try:
            holder_plenary.write(locked=True)
        except IncompleteError:
            holder_plenary.cleanup(domain, locked=True)

        remove_plenary.remove(locked=True)

        if dsdb_callback:
            dsdb_callback(session, logger, holder, dbresource, **arguments)
    except:
        holder_plenary.restore_stash()
        remove_plenary.restore_stash()
        raise
    finally:
        lock_queue.release(key)

    return


def add_resource(session, logger, holder, dbresource, dsdb_callback=None,
                 **arguments):
    if dbresource not in holder.resources:
        holder.resources.append(dbresource)

    holder_plenary = Plenary.get_plenary(holder.holder_object, logger=logger)
    res_plenary = Plenary.get_plenary(dbresource, logger=logger)

    domain = holder.holder_object.branch.name

    session.flush()

    key = CompileKey.merge([res_plenary.get_write_key(),
                            holder_plenary.get_write_key()])
    try:
        lock_queue.acquire(key)
        res_plenary.write(locked=True)
        try:
            holder_plenary.write(locked=True)
        except IncompleteError:
            holder_plenary.cleanup(domain, locked=True)

        if dsdb_callback:
            dsdb_callback(session, logger, dbresource, **arguments)

    except:
        res_plenary.restore_stash()
        holder_plenary.restore_stash()
        raise
    finally:
        lock_queue.release(key)

    return

def walk_resources(dbobj):
    """
    Walk all resources of a resource holder

    Resource groups are expanded in a depth-first manner.
    """

    if not dbobj.resholder:
        return
    for res in dbobj.resholder.resources:
        if isinstance(res, ResourceGroup):
            walk_resources(res)
        else:
            yield res
