#!/ms/dist/python/PROJ/core/2.5.0/bin/python
import sys
import msversion

#msversion.addpkg('sqlalchemy', '0.4.7', 'dev')
msversion.addpkg('sqlalchemy', '0.5beta', 'dev')

msversion.addpkg('cx_Oracle','4.4-10.2.0.1','dev')

#if '--debug' in sys.argv:
msversion.addpkg('ipython','0.8.2','dist')

#from IPython.Shell import IPShellEmbed
#banner  = '***Embedded IPython, Ctrl-D to quit.'
#args    = []
#ipshell = IPShellEmbed(args,banner=banner)

#if not sys.modules.has_key('migrate.changeset'):
#    msversion.addpkg('sqlalchemy-migrate', '0.4.4', 'dev')
