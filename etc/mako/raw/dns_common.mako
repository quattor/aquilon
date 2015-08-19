<%def name="dns_record_head(record)">\
${"{0:c}: {0.fqdn!s}".format(record)}
  DNS Environment: ${record.fqdn.dns_environment.name}
%if record.hardware_entity:
  Primary Name Of: ${record.hardware_entity._get_class_label()} ${record.hardware_entity.label}
%endif
## The alias_cnt property can be loaded eagerly, so use it to check the
## presence of aliases before trying to query the alias table itself
%if record.alias_cnt:
  Aliases: ${", ".join(str(a.fqdn) + ("" if a.fqdn.dns_environment == record.fqdn.dns_environment else " [environment: " + a.fqdn.dns_environment.name + "]") for a in record.all_aliases)}
%endif
%if record.address_alias_cnt:
  Address Aliases: ${", ".join(str(a.fqdn) + ("" if a.fqdn.dns_environment == record.fqdn.dns_environment else " [environment: " + a.fqdn.dns_environment.name + "]") for a in record.all_address_aliases)}
%endif
%if record.ttl:
  TTL: ${record.ttl}
%endif
%if record.owner_grn:
  Owned by GRN: ${record.owner_grn}
%endif
</%def>
<%def name="dns_record_tail(record)">\
%if record.comments:
  Comments: ${record.comments | trim}
%endif
</%def>
