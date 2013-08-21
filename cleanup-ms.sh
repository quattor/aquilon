%setup -n %{name}-%{unmangled_version}
pwd
grep -lr 'import aquilon.*depends' .|xargs sed -i '/import aquilon.*depends/d'
