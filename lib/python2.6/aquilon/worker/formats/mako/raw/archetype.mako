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
% if record.comments:
  Comments: ${record.comments}
% endif
