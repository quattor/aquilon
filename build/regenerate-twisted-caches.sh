python -c 'from twisted.plugin import IPlugin, getPlugins; list(getPlugins(IPlugin))'
if ! getent passwd aquilon &> /dev/null
then
    useradd aquilon -s /usr/bin/git-shell -d /var/quattor -m
fi
