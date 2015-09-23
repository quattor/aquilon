<%namespace name="dns_common" file="/dns_common.mako"/>\
${dns_common.dns_record_head(record)}\
  IP: ${record.ip}
  Network: ${record.network}
  Network Environment: ${record.network.network_environment.name}
%if record.assignments:
  Assigned To: ${", ".join("%s/%s" % (addr.interface.hardware_entity.label, addr.interface.name) for addr in record.assignments)}
%endif
%if record.service_addresses:
% for service_address in record.service_addresses:
  Provides: ${format(service_address)}
    Bound to: ${format(service_address.holder)}
% endfor
%endif
%if record.reverse_ptr:
  Reverse PTR: ${str(record.reverse_ptr)}
%endif
${dns_common.dns_record_tail(record)}\
