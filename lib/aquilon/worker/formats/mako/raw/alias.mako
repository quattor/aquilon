<%namespace name="dns_common" file="/dns_common.mako"/>\
${dns_common.dns_record_head(record)}\
  Target: ${str(record.target)}
${dns_common.dns_record_tail(record)}\
