<%
    flags = []
    if record.is_compileable:
        flags.append("compilable")
    flagstr = ""
    if len(flags) != 0:
        flagstr = " [" + " ".join(flags) + "] "
%>\
Archetype: ${record.name}${flagstr}
% for service in record.services:
  Required Service: ${service.name}
% endfor
% if record.comments:
  Comments: ${record.comments}
% endif
