% if record.cluster:
Member of ${"{0:c}".format(record.cluster)}: ${record.cluster.name}
% endif
${formatter.redirect_raw(record.personality)}
${formatter.redirect_raw(record.archetype)}
${formatter.redirect_raw(record.operating_system)}
% if record.branch.branch_type == 'domain':
Domain: ${record.branch.name}
% else:
Sandbox: ${record.sandbox_author.name}/${record.branch.name}
% endif
${formatter.redirect_raw(record.status)}
% for build_item in record.services_used:
Template: ${build_item.cfg_path}
% endfor
% if record.comments:
Comments: ${record.comments}
% endif
