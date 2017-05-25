Description
===========
Aquilon is the third generation of the Quattor configuration database. This is the
recommended one for every new Quattor site.

Aquilon documentation can be found on the Quattor
[web site](http://www.quattor.org/aquilon/00-install.html).

Development
===========
Commit messages require a `Change-Id:` line. Simply add the [gerrit `commit-msg` hook](https://gerrit.googlesource.com/gerrit/+/master/gerrit-server/src/main/resources/com/google/gerrit/server/tools/root/hooks/commit-msg)

You can (try to) use following commands (will overwrite previous `commit-msg` script):

    wget -q -O - "https://gerrit.googlesource.com/gerrit/+/master/gerrit-server/src/main/resources/com/google/gerrit/server/tools/root/hooks/commit-msg?format=TEXT" | base64 --decode > .git/hooks/commit-msg
    chmod +x .git/hooks/commit-msg
