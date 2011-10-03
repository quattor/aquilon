<%namespace name="dns_common" file="/dns_common.mako"/>\
${dns_common.dns_record_head(record)}\
  Service: ${record.service}
  Protocol: ${record.protocol}
  Priority: ${record.priority}
  Weight: ${record.weight}
  Target: ${record.target.fqdn}
  Port: ${record.port}
${dns_common.dns_record_tail(record)}\
