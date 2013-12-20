%setup -n %{name}-%{unmangled_version}
grep -lrE '(import aquilon.*depends)|(from aquilon.*import depends)' . \
    |xargs sed -i '/\(import aquilon.*depends\)\|\(from aquilon.*import depends\)/d'
stylesheets=$(echo /usr/share/sgml/docbook/xsl*stylesheets-*)
sed -i '/ms.version/d' bootstrap/gen_completion.py
sed -i "s:/ms/dist/fsf/PROJ/docbook-xsl-ns/.*/common:$stylesheets:" \
    doc/style-man.xsl
sed -i "s:/ms/dist/fsf/PROJ/docbook-xsl-ns/.*/common:$stylesheets:" \
    doc/style-html.xsl
