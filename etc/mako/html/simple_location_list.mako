<ul>
% for loc in record:
  <li><a href="/location/${loc.location_type}/${loc.name}.html">${loc.name}</a></li>
% endfor
</ul>