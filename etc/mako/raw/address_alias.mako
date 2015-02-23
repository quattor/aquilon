<%namespace name="dns_common" file="/dns_common.mako"/>\
${dns_common.dns_record_head(record)}\
  Target: ${record.target.fqdn + " [" + str(record.target_ip) + ("" if record.fqdn.dns_environment == record.target.dns_environment else ", environment: " + record.target.dns_environment.name) + "]"}
${dns_common.dns_record_tail(record)}\
