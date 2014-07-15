# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2013,2014  Contributor
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


import os
import time
import socket
import logging
import gzip

from xml.etree import ElementTree

from aquilon.aqdb.model import Service
from aquilon.utils import write_file, remove_file

LOGGER = logging.getLogger(__name__)

CCM_NOTIF = 1
CDB_NOTIF = 2

NOTIFICATION_TYPES = {CCM_NOTIF: "ccm", CDB_NOTIF: "cdb"}

try:
    CDPPORT = socket.getservbyname("cdp")
except:  # pragma: no cover
    CDPPORT = 7777


def build_index(config, session, logger=LOGGER):
    '''
    Create an index of what profiles are available

    Compare the mtimes of everything in profiledir against
    an index file (profiles-info.xml). Produce a new index
    and send out notifications to "server modules" (as defined
    within the broker configuration).
    '''
    gzip_output = config.getboolean('panc', 'gzip_output')
    transparent_gzip = config.getboolean('panc', 'transparent_gzip')
    gzip_index = gzip_output and transparent_gzip

    profilesdir = config.get("broker", "profilesdir")

    # Profiles are xml or json files, and can be configured to (additionally) be gzip'd
    if config.getboolean('panc', 'gzip_output'):
        compress_suffix = ".gz"
    else:
        compress_suffix = ""

    suffixes = [".xml" + compress_suffix, ".json" + compress_suffix]

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
            tree = ElementTree.parse(source)
            for profile in tree.getiterator("profile"):
                if not profile.text or "mtime" not in profile.attrib:
                    continue
                mtime = int(profile.attrib["mtime"])

                obj = profile.text.strip()
                if not obj:
                    continue

                # If the broker configuration changes, the old index may
                # still contain extensions we no longer want to
                # generate, so we have to handle all possible values
                # here
                for ext in [".xml", ".xml.gz", ".json", ".json.gz"]:
                    if obj.endswith(ext):
                        obj = obj[:-len(ext)]
                        break

                if obj not in old_object_index or old_object_index[obj] < mtime:
                    old_object_index[obj] = mtime
        except Exception as e:  # pragma: no cover
            logger.info("Error processing %s, continuing: %s",
                        index_path, e)
        finally:
            if source:
                source.close()

    # modified_index stores the subset of namespaced names that
    # have changed since the last index. The values are unused.
    modified_index = {}

    # objects stores the (mtime, suffix) pairs we discovered. Its purpose is
    # de-duplicating if there are multiple suffixes (say, both .json and .xml)
    # for the same object - we want to advertise only the newest.
    objects = {}

    # Old profiles that should be cleaned up, if the profile extension changes
    cleanup = []

    for root, _dirs, files in os.walk(profilesdir):
        for profile in files:
            if profile == profile_index:
                continue

            for suffix in suffixes:
                if not profile.endswith(suffix):
                    continue

                obj = os.path.join(root, profile[:-len(suffix)])

                # Remove the common prefix: our profilesdir, so that the
                # remaining object name is relative to that root (+1 in order
                # to remove the slash separator)
                obj = obj[len(profilesdir) + 1:]

                # This operation is not done with a lock, and it's possible
                # that the file has been removed since calling os.walk().
                # If that's the case, no need to add it to the modified_index.
                try:
                    mtime = os.path.getmtime(os.path.join(root, profile))
                except OSError as e:
                    continue

                if obj in old_object_index:
                    if mtime > old_object_index[obj]:
                        modified_index[obj] = mtime

                    # Note this test means stale profiles will be cleaned up the
                    # second time the index is rebuilt: the first time the
                    # profile's mtime will still match the old index
                    if mtime < old_object_index[obj]:
                        cleanup.append(os.path.join(root, profile))

                # The index generally just lists whatever is produced.  However,
                # the webserver may be configured to transparently serve up
                # .xml.gz files when just the .xml is requested.  In this case,
                # the index should just list (advertise) the profile as a .xml
                # file.
                if transparent_gzip:
                    advertise_suffix = suffix.rstrip(".gz")
                else:
                    advertise_suffix = suffix

                if obj not in objects or objects[obj][0] < mtime:
                    objects[obj] = (mtime, advertise_suffix)

    content = []
    content.append("<?xml version='1.0' encoding='utf-8'?>")
    content.append("<profiles>")
    for obj, (mtime, advertise_suffix) in objects.items():
        content.append("<profile mtime='%d'>%s%s</profile>" %
                       (mtime, obj, advertise_suffix))
    content.append("</profiles>")

    compress = None
    if gzip_index:
        compress = 'gzip'
    write_file(index_path, "\n".join(content), logger=logger, compress=compress)

    logger.debug("Updated %s, %d objects modified", index_path,
                 len(modified_index))

    for filename in cleanup:
        logger.debug("Cleaning up %s" % filename)
        remove_file(filename, logger=logger)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if config.has_option("broker", "bind_address"):
        bind_address = socket.gethostbyname(config.get("broker", "bind_address"))
        if config.has_option("broker", "cdp_send_port"):  # pragma: no cover
            port = config.get_int("broker", "cdp_send_port")
        else:
            port = 0
        sock.bind((bind_address, port))

    if config.has_option("broker", "server_notifications"):
        servers = set()
        for service in config.get("broker", "server_notifications").split():
            if service.strip():
                try:
                    # service may be unknown
                    srvinfo = Service.get_unique(session, service, compel=True)
                    for instance in srvinfo.instances:
                        servers.update([srv.fqdn for srv in instance.servers])
                except Exception as e:
                    logger.info("failed to lookup up server module %s: %s",
                                service, e)
        count = send_notification(CDB_NOTIF, servers, sock=sock,
                                  logger=logger)
        logger.info("sent %d server notifications", count)

    if (config.has_option("broker", "client_notifications")
        and config.getboolean("broker", "client_notifications")):  # pragma: no cover
        count = send_notification(CCM_NOTIF, modified_index.keys(), sock=sock,
                                  logger=logger)
        logger.info("sent %d client notifications", count)

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

        except Exception as e:
            logger.info("Error notifying %s: %s", host, e)

    return success


def trigger_notifications(config, logger=LOGGER, loglevel=logging.INFO):
    sockname = os.path.join(config.get("broker", "sockdir"), "notifysock")
    sd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    logger.debug("Attempting connection to notification socket: %s", sockname)
    try:
        sd.connect(sockname)
    except socket.error as err:
        logger.error("Failed to connect to notification socket: %s", err)

    try:
        sd.send("update")
    except socket.error as err:
        logger.error("Failed to send to notification socket: %s", err)

    sd.close()

    logger.log(loglevel, "Index rebuild and notifications will happen in "
               "the background.")
