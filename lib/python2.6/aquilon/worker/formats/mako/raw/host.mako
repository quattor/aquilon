% if record.cluster:
Member of ${"{0:c}".format(record.cluster)}: ${record.cluster.name}
% endif
% for resource in record.resources:
${formatter.redirect_raw(resource)}
%endfor
${formatter.redirect_raw(record.personality)}
${formatter.redirect_raw(record.archetype)}
${formatter.redirect_raw(record.operating_system)}
% if record.branch.branch_type == 'domain':
Domain: ${record.branch.name}
% else:
Sandbox: ${record.sandbox_author.name}/${record.branch.name}
% endif
${formatter.redirect_raw(record.status)}
Advertise Status: ${str(record.advertise_status)}
% for grn in record.grns:
GRN: ${grn.grn}
% endfor
% for si in record.services_used:
Template: ${si.cfg_path}
% endfor
% for si in record.services_provided:
Provides: ${si.cfg_path}
% endfor
% if record.comments:
Comments: ${record.comments}
% endif
