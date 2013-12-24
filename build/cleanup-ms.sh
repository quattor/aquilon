%setup -n %{name}-%{unmangled_version}
grep -lrE '(import aquilon.*depends)|(from aquilon.*import depends)' . \
    |xargs sed -i '/\(import aquilon.*depends\)\|\(from aquilon.*import depends\)/d'
stylesheets=/usr/share/sgml/docbook/xsl-stylesheets-$(rpm -q --qf %{VERSION} \
    docbook5-style-xsl)
sed -i '/ms.version/d' bootstrap/gen_completion.py
sed -i "s:/ms/dist/fsf/PROJ/docbook-xsl-ns/.*/common:$stylesheets:" \
    doc/style-man.xsl
sed -i "s:/ms/dist/fsf/PROJ/docbook-xsl-ns/.*/common:$stylesheets:" \
    doc/style-html.xsl
