<%namespace name="dns_common" file="/dns_common.mako"/>\
${dns_common.dns_record_head(record)}\
  Target: ${str(record.target)}
%if record.services_provided:
%  for srv in record.services_provided:
  Provides Service: ${srv.service_instance.service.name} Instance: ${srv.service_instance.name}
%  endfor
%endif
${dns_common.dns_record_tail(record)}\
