%setup -n %{name}-%{unmangled_version}
grep -lrE '(import aquilon.*depends)|(from aquilon.*import depends)' . \
    |xargs sed -i '/\(import aquilon.*depends\)\|\(from aquilon.*import depends\)/d'
sed -i '/ms.version/d' bootstrap/gen_completion.py
