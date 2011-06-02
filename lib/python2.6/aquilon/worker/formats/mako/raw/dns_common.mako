<%def name="dns_record_head(record)">\
${"{0:c}: {0.fqdn!s}".format(record)}
  DNS Environment: ${record.fqdn.dns_environment.name}
%if record.hardware_entity:
  Primary Name Of: ${record.hardware_entity._get_class_label()} ${record.hardware_entity.label}
%endif
## The alias_cnt property can be loaded eagerly, so use it to check the
## presence of aliases before trying to query the alias table itself
%if record.alias_cnt:
  Aliases: ${", ".join([str(a.fqdn) for a in record.all_aliases])}
%endif
</%def>
<%def name="dns_record_tail(record)">\
%if record.comments:
  Comments: ${record.comments | trim}
%endif
</%def>
