
import os
import time
import socket
import xml.etree.ElementTree as ET
from aquilon.server.dbwrappers.service import get_service
from twisted.python import log
from aquilon.server.processes import write_file


CCM_NOTIF = 1
CDB_NOTIF = 2

NOTIFICATION_TYPES = {
        CCM_NOTIF : "ccm",
        CDB_NOTIF : "cdb"
}

def build_index(config, session, profilesdir, clientNotify=True):
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
    profile_index = "profiles-info.xml"

    old_object_index = {}
    index_path = os.path.join(profilesdir, profile_index)
    if os.path.exists(index_path):
        try:
            tree = ET.parse(index_path)
            for profile in tree.getiterator("profile"):
                if (profile.text and profile.attrib.has_key("mtime")):
                    object = profile.text.strip()
                    if object:
                        if object.endswith(".xml"):
                            object = object[:-4]
                        old_object_index[object] = int(profile.attrib["mtime"])
        except Exception, e:
            log.msg("Error processing %s, continuing: %s" % (index_path, e))

    object_index = {}
    modified_index = {}
    for profile in os.listdir(profilesdir):
        if profile == profile_index:
            continue
        if not profile.endswith(".xml"):
            continue
        object = profile[:-4]
        object_index[object] = os.path.getmtime(
                os.path.join(profilesdir, profile))
        if (old_object_index.has_key(object)
                and object_index[object] > old_object_index[object]):
            #log.msg("xml for %s has a newer mtime, will notify" % host)
            modified_index[object] = object_index[object]

    content = []
    content.append("<?xml version='1.0' encoding='utf-8'?>")
    content.append("<profiles>")
    for object, mtime in object_index.items():
        content.append("<profile mtime='%d'>%s.xml</profile>"
                % (mtime, object))
    content.append("</profiles>")

    write_file(index_path, "\n".join(content))

    if config.has_option("broker", "server_notifications"):
        service_modules = {}
        for service in config.get("broker", "server_notifications").split():
            if service.strip():
                try:
                    # service may be unknown
                    srvinfo = get_service(session, service)
                    for instance in srvinfo.instances:
                        for sis in instance.servers:
                            service_modules[sis.system.fqdn] = 1
                except Exception, e:
                    log.msg("failed to lookup up server module %s: %s" % (service, e))
        send_notification(CDB_NOTIF, service_modules.keys())

    if (config.has_option("broker", "client_notifications")
        and config.getboolean("broker", "client_notifications")
        and clientNotify):
        send_notification(CCM_NOTIF, modified_index.keys())

def send_notification(ntype, machines):
    '''send CDP notification messages to a list of hosts. This
    are sent synchronously, but we don't wait (or care) for any
    reply, so it shouldn't be a problem.
    type should be CCM_NOTIF or CDB_NOTIF
    '''
    packet = NOTIFICATION_TYPES[ntype] + "\0" + str(int(time.time()))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        port = socket.getservbyname("cdp")
    except:
        port = 7777

    for host in machines:
        try:
            ip = socket.gethostbyname(host)
            log.msg("Sending %s notification to %s"
                    % (NOTIFICATION_TYPES[ntype], host))
            sock.sendto(packet, (ip, port))

        except socket.gaierror:
            # This host is not known (yet), so we silently
            # discard the notification.
            pass

        except Exception, e:
            log.msg("Error notifying %s: %s" % (host, e))

