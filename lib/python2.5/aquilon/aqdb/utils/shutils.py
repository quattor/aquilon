""" Wrapper for ipshell, and associated utility functions """

import sys
import os
import tempfile
import subprocess as sp
from sqlalchemy.orm import class_mapper

from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.utils.schema2dot import create_schema_graph

from IPython.Shell import IPShellEmbed
_banner  = '***Embedded IPython, Ctrl-D to quit.'
_args    = []
ipshell = IPShellEmbed(_args, banner=_banner)

def load_all(verbose=True):
    import aquilon.aqdb
    for i in aquilon.aqdb.__all__:
        print "Importing aquilon.aqdb.%s" % i
        __import__("aquilon.aqdb.%s" % i)
        mod = getattr(aquilon.aqdb, i)
        if hasattr(mod, "__all__"):
            for j in mod.__all__:
                print "Importing aquilon.aqdb.%s.%s" % (i, j)
                __import__("aquilon.aqdb.%s.%s" % (i, j))

def _setup_graphviz():
    if os.environ['PATH'].find('graphviz') < 0:
        from aquilon.config import Config
        from ConfigParser   import NoOptionError

        try:
            c = Config()
        except Exception, e:
            print >> sys.stderr, "failed to read configuration: %s" % e
            sys.exit(os.EX_CONFIG)

        try:
            _GRAPHVIZ = c.get('DEFAULT', 'graphviz_dir')
        except NoOptionError:
            _GRAPHVIZ='/ms/dist/fsf/PROJ/graphviz/2.6/bin'

        assert _GRAPHVIZ
        os.environ['PATH'] += ':%s'%(_GRAPHVIZ)
        return _GRAPHVIZ

#TODO: schema/uml as an argument (DRY)
def write_schema_graph(db, image_name = "/tmp/aqdb_schema.png"):
    gv_path = _setup_graphviz()
    try:
        temp_fd, temp_file_name = tempfile.mkstemp(prefix='aqdbGraph',
                                                   suffix='.dot',
                                                   dir='/tmp')
        graph = create_schema_graph(metadata = db.meta)
        graph.write_dot(temp_file_name)
        cmd = '%s/dot -Tpng -o %s %s'%(gv_path, image_name, temp_file_name)
        #print 'running %s'%(cmd)
        p = sp.Popen(cmd, shell  = True, stdout = sp.PIPE, stderr = sp.PIPE)
        out,err = p.communicate()
        if out:
            print out
            return False
        elif err:
            print err
            return False
        else:
            return True
    finally:
        os.close(temp_fd)
        os.remove(temp_file_name)
    #TODO: use PIL's show/save_schema_graph(db, name)

def write_uml_graph(db, image_name = "aqdb_classes.dot"):
    pass
#TODO: not totally working yet...seems to hang.
#from aquilon.aqdb.utils.schema2dot import create_schema_graph
#                                           create_uml_graph,
#                                           show_schema_graph,
#                                           show_uml_graph)
#def write_uml_graph(db, image_name = "aqdb_classes.dot"):
#    gv_path = _setup_graphviz()
#    Base.metadata = db.meta
#    graph = create_uml_graph(
#              [class_mapper(c) for c in Base._decl_class_registry.itervalues()])
#    graph.write_dot(name)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

