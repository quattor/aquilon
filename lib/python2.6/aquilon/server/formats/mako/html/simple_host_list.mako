<ul>
% for host in record:
  <li><a href="/host/${host.fqdn}.html">${host.fqdn}</a></li>
% endfor
</ul>
