<%
    flags = []
    if record.is_compileable:
        flags.append("compilable")
    flagstr = ""
    if len(flags) != 0:
        flagstr = " [" + " ".join(flags) + "] "
    desc = ""
    if record.cluster_type is not None:
        desc = "Cluster"
    else:
        desc = "Host"
%>\
${desc} Archetype: ${record.name}${flagstr}
% for service in record.services:
  Required Service: ${service.name}
% endfor
% for link in record.features:
<%
      if link.feature.post_personality:
          flagstr = ' [post_personality]'
      elif link.feature.post_personality_allowed:
          flagstr = ' [pre_personality]'
      else:
          flagstr = ''
%>\
  ${"{0:c}: {0.name}{1}".format(link.feature, flagstr)}
% if link.model:
    Vendor: ${link.model.vendor.name} Model: ${link.model.name}
% endif
% endfor
% if record.comments:
  Comments: ${record.comments}
% endif
