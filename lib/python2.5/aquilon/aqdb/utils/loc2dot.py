import os
import sys
import types
import ms.version

if not sys.modules.has_key('pyparsing'):
    ms.version.addpkg('pyparsing', '1.5.0')
    import pyparsing

if not sys.modules.has_key('pydot'):
    ms.version.addpkg('pydot', '1.0.2')
    import pydot

    #graph = pydot.Dot(prog="dot", mode="ipsep", overlap="ipsep", sep="0.01",
    #                  concentrate=concentrate, rankdir=rankdir)

    #for table in tables:
    #    graph.add_node(pydot.Node(str(table.name),
    #        shape="plaintext",
    #        label=_render_table_html(table, metadata, 
    #                                 show_indexes, show_datatypes),
    #        fontname=font, fontsize="7.0"))

#def show_schema_graph(db, name, *args, **kwargs):
#    from cStringIO import StringIO
#    from PIL import Image
#    iostream = StringIO(create_schema_graph(db, name).create_png())
    #Image.open(iostream).show(command=kwargs.get('command','gwenview'))
#    Image.open(iostream).save(name)
