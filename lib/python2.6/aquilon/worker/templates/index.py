# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011  Contributor
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
import time
import socket
import logging
import gzip

import xml.etree.ElementTree as ET

from aquilon.worker.processes import write_file
from aquilon.worker.logger import CLIENT_INFO
from aquilon.aqdb.model import Service

LOGGER = logging.getLogger(__name__)

CCM_NOTIF = 1
CDB_NOTIF = 2

NOTIFICATION_TYPES = {CCM_NOTIF: "ccm", CDB_NOTIF: "cdb"}

try:
    CDPPORT = socket.getservbyname("cdp")
except:  # pragma: no cover
    CDPPORT = 7777


def build_index(config, session, profilesdir, clientNotify=True,
                logger=LOGGER):
    '''
    Create an index of what profiles are available

    Compare the mtimes of everything in profiledir against
    an index file (profiles-info.xml). Produce a new index
    and send out notifications to "server modules" (as defined
    within the broker configuration). If clientNotify
    is True, then individual notifications are also sent
    to each host. If clientNotify is False, then the server modules
    will still be notified, but there is no processing of the
    individual hosts. Note that the broker has a config option
    send_notifications, which if false will turn off notifications
    unconditionally. Only if the broker config allows will the
    clientNotify be checked.

    '''
    gzip_output = config.getboolean('panc', 'gzip_output')
    gzip_as_xml = config.getboolean('panc', 'advertise_gzip_as_xml')
    gzip_index = gzip_output and gzip_as_xml

    # Profiles are xml files, and can be configured to (additionally) be gzip'd
    profile_suffix = '.xml'
    if gzip_output:
        profile_suffix += '.gz'

    # The index generally just lists whatever is produced.  However, the
    # webserver may be configured to transparently serve up .xml.gz files
    # when just the .xml is requested.  In this case, the index should just
    # list (advertise) the profile as a .xml file.
    advertise_suffix = profile_suffix
    if gzip_as_xml:
        advertise_suffix = '.xml'

    # The profile should be .xml, unless webserver trickery is going to
    # redirect all requests for .xml files to be .xml.gz requests. :)
    profile_index = 'profiles-info.xml'
    if gzip_index:
        profile_index += '.gz'

    old_object_index = {}
    index_path = os.path.join(profilesdir, profile_index)
    source = None
    if os.path.exists(index_path):
        try:
            if gzip_index:
                source = gzip.open(index_path)
            else:
                source = open(index_path)
            tree = ET.parse(source)
            for profile in tree.getiterator("profile"):
                if (profile.text and "mtime" in profile.attrib):
                    obj = profile.text.strip()
                    if obj:
                        if obj.endswith(".xml"):
                            obj = obj[:-4]
                        elif obj.endswith(".xml.gz"):
                            obj = obj[:-7]
                        old_object_index[obj] = int(profile.attrib["mtime"])
        except Exception, e:  # pragma: no cover
            logger.info("Error processing %s, continuing: %s" %
                        (index_path, e))
        finally:
            if source:
                source.close()

    # object_index ties namespaced files to mtime
    object_index = {}
    # modified_index stores the subset of namespaced names that
    # have changed since the last index. The values are unused.
    modified_index = {}

    for root, _dirs, files in os.walk(profilesdir):
        for profile in files:
            if profile == profile_index:
                continue
            if not profile.endswith(profile_suffix):
                continue
            obj = os.path.join(root, profile[:-len(profile_suffix)])
            # Remove the common prefix: our profilesdir, so that the
            # remaining object name is relative to that root (+1 in order
            # to remove the slash separator)
            obj = obj[len(profilesdir) + 1:]
            # This operation is not done with a lock, and it's possible
            # that the file has been removed since calling os.walk().
            # If that's the case, no need to add it to the modified_index.
            try:
                object_index[obj] = os.path.getmtime(os.path.join(root,
                                                                  profile))
            except OSError, e:
                continue
            if (obj in old_object_index and
                object_index[obj] > old_object_index[obj]):
                modified_index[obj] = object_index[obj]

    content = []
    content.append("<?xml version='1.0' encoding='utf-8'?>")
    content.append("<profiles>")
    for obj, mtime in object_index.items():
        content.append("<profile mtime='%d'>%s%s</profile>" %
                       (mtime, obj, advertise_suffix))
    content.append("</profiles>")

    compress = None
    if gzip_index:
        compress = 'gzip'
    write_file(index_path, "\n".join(content), logger=logger,
               compress=compress)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if config.has_option("broker", "bind_address"):
        bind_address = socket.gethostbyname(config.get("broker", "bind_address"))
        if config.has_option("broker", "cdp_send_port"):  # pragma: no cover
            port = config.get_int("broker", "cdp_send_port")
        else:
            port = 0
        sock.bind((bind_address, port))

    if config.has_option("broker", "server_notifications"):
        service_modules = {}
        for service in config.get("broker", "server_notifications").split():
            if service.strip():
                try:
                    # service may be unknown
                    srvinfo = Service.get_unique(session, service, compel=True)
                    for instance in srvinfo.instances:
                        for fqdn in instance.server_fqdns:
                            service_modules[fqdn] = 1
                except Exception, e:
                    logger.info("failed to lookup up server module %s: %s" %
                                (service, e))
        count = send_notification(CDB_NOTIF, service_modules.keys(), sock=sock,
                                  logger=logger)
        logger.log(CLIENT_INFO, "sent %d server notifications" % count)

    if (config.has_option("broker", "client_notifications")
        and config.getboolean("broker", "client_notifications")
        and clientNotify):  # pragma: no cover
        count = send_notification(CCM_NOTIF, modified_index.keys(), sock=sock,
                                  logger=logger)
        logger.log(CLIENT_INFO, "sent %d client notifications" % count)

    sock.close()


def send_notification(ntype, modified, sock=None, logger=LOGGER):
    '''send CDP notification messages to a list of hosts.

    This are sent synchronously, but we don't wait (or care) for any
    reply, so it shouldn't be a problem. type should be CCM_NOTIF or CDB_NOTIF.
    'modified' is a dict of object names that may be namespaced. Object
    names that cannot be looked up in DNS are silently ignored.
    Returns the number of notifications that were sent.
    '''

    success = 0
    for obj in modified:
        # We need to clean the name, since it might
        # be namespaced. This (in effect) globalizes
        # all names. Perhaps we might want to do some
        # checks based on the namespace. Not for now.
        (_ns, _sep, host) = obj.rpartition('/')

        try:
            # If you think it would be a good idea to look up the IP address
            # from the DB directly, then think about the case when the IP
            # address of a host changes: the DB contains the new address, but
            # the host still uses the old. Relying on DNS here means that the
            # notification goes to the right place.
            ip = socket.gethostbyname(host)
            packet = NOTIFICATION_TYPES[ntype] + "\0" + str(int(time.time()))
            sock.sendto(packet, (ip, CDPPORT))
            success = success + 1

        except socket.gaierror:
            # This hostname is unknown, so we silently
            # discard the notification.
            pass

        except Exception, e:
            logger.info("Error notifying %s: %s" % (host, e))

    return success
