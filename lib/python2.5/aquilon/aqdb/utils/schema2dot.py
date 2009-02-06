import os
import sys
import types
import tempfile
import cStringIO
import ms.version
import subprocess as sp

if not sys.modules.has_key('pyparsing'):
    ms.version.addpkg('pyparsing', '1.5.0', 'dist')
    import pyparsing

if not sys.modules.has_key('pydot'):
    ms.version.addpkg('pydot', '1.0.2', 'dist')
    import pydot

if not sys.modules.has_key('sqlalchemy'):
    ms.version.addpkg('sqlalchemy', '0.5.0') #TODO: REMOVE THIS STANZA!
    import sqlalchemy
    import warnings
    #warnings.warn('schema2dot: loading sqlalchemy on my own')

if not sys.modules.has_key('pil'):
    ms.version.addpkg('pil','1.1.6')
from PIL import Image

if not sys.modules.has_key('ms.modulecmd'):
    ms.version.addpkg("ms.modulecmd", "1.0.0")
from ms.modulecmd import Modulecmd

m = Modulecmd()
m.load('fsf/graphviz/2.6')

#TODO:put this in the module itself, not here
_LIBTOOL_PATH = '/ms/dist/fsf/PROJ/libtool/1.5.18/lib'
#TODO: also, the empty path is a bug!
if os.environ.get('LD_LIBRARY_PATH', None):
    os.environ['LD_LIBRARY_PATH'] += ':' + _LIBTOOL_PATH
else:
    os.environ['LD_LIBRARY_PATH'] = _LIBTOOL_PATH

from sqlalchemy.orm import sync
from sqlalchemy import Table, text
from sqlalchemy.orm.properties import PropertyLoader
from sqlalchemy.databases.postgres import PGDialect

__all__ = ['show_schema_graph', 'create_schema_graph']
           #, 'show_uml_graph', 'create_uml_graph']

def create_uml_graph(mappers,
                     show_operations=True,
                     show_attributes=True,
                     show_multiplicity_one=False,
                     show_datatypes=True,
                     linewidth="1.0",
                     font="Sans-Serif"):

    graph = pydot.Dot(prog='neato', mode="major", overlap="0", sep="0.01",
                      pack="True",dim="3")
    relations = set()

    for mapper in mappers:
        graph.add_node(
            pydot.Node(mapper.class_.__name__, shape="plaintext",
                       label=_mk_label(mapper, show_operations,
                                       show_attributes, show_datatypes,
                                       linewidth), fontname=font,
                                       fontsize="8.0"))
        if mapper.inherits:
            graph.add_edge(
                pydot.Edge(mapper.inherits.class_.__name__,
                           mapper.class_.__name__,
                           arrowhead='none',
                           arrowtail='empty',
                           style="setlinewidth(%s)" % linewidth,
                           arrowsize=linewidth))

        for loader in mapper.iterate_properties:
            if isinstance(loader, PropertyLoader) and loader.mapper in mappers:
                if hasattr(loader, 'reverse_property'):
                    relations.add(frozenset([loader, loader.reverse_property]))
                else:
                    relations.add(frozenset([loader]))

    for relation in relations:
        args = {}
        def multiplicity_indicator(prop):
            if prop.uselist:
                return ' *'
            if any(col.nullable for col in prop.local_side):
                return ' 0..1'
            if show_multiplicity_one:
                return ' 1'
            return ''

        if len(relation) == 2:
            src, dest = relation
            from_name = src.parent.class_.__name__
            to_name = dest.parent.class_.__name__

            def calc_label(src,dest):
                return '+' + src.key + multiplicity_indicator(src)
            args['headlabel'] = calc_label(src,dest)

            args['taillabel'] = calc_label(dest,src)
            args['arrowtail'] = 'none'
            args['arrowhead'] = 'none'
            args['constraint'] = False
        else:
            prop, = relation
            from_name = prop.parent.class_.__name__
            to_name = prop.mapper.class_.__name__
            args['headlabel'] = '+%s%s' % (prop.key, multiplicity_indicator(prop))
            args['arrowtail'] = 'none'
            args['arrowhead'] = 'vee'

        graph.add_edge(pydot.Edge(from_name,to_name,
            fontname=font, fontsize="7.0", style="setlinewidth(%s)"%linewidth, arrowsize=linewidth,
            **args)
        )

    return graph

def create_schema_graph(tables=None,
                        metadata=None,
                        show_indexes=True,
                        show_datatypes=True,
                        font="Sans-Serif",
                        concentrate="True",
                        relation_options={},
                        rankdir='TB'):
    relation_kwargs = {'fontsize':"7.0"}
    relation_kwargs.update(relation_options)

    if not metadata and len(tables):
        metadata = tables[0].metadata
    elif not tables and metadata:
        if not len(metadata.tables):
            metadata.reflect()
        tables = metadata.tables.values()
    else:
        raise Exception("You need to specify at least tables or metadata")

    graph = pydot.Dot(prog="dot", mode="ipsep", overlap="ipsep", sep="0.01",
                      concentrate=concentrate, rankdir=rankdir)
    for table in tables:
        graph.add_node(pydot.Node(str(table.name),
            shape="record",
            label=_render_table_record(table, metadata,
                                     show_indexes, show_datatypes),
            fontname=font, fontsize="7.0"))

    for table in tables:
        for fk in table.foreign_keys:
            edge = [table.name, fk.column.table.name]
            is_inheritance = fk.parent.primary_key and fk.column.primary_key
            if is_inheritance:
                edge = edge[::-1]
            graph_edge = pydot.Edge(
                headlabel="+ %s"%fk.column.name, taillabel='+ %s'%fk.parent.name,
                arrowhead=is_inheritance and 'none' or 'odot' ,
                arrowtail=(fk.parent.primary_key or
                           fk.parent.unique) and 'empty' or 'crow' ,
                fontname=font, *edge, **relation_kwargs)

            graph_edge.set_parent_graph(graph.get_parent_graph)
            graph.add_edge(graph_edge)
    return graph

def show_uml_graph(db,image_name='/tmp/aqdb_uml.png', *args, **kw):
    ios = cStringIO.StringIO(create_uml_graph(
        [class_mapper(c) for c in Base._decl_class_registry.itervalues()])).create_png()
    Image.open(ios).save(image_name)

def show_schema_graph(db, image_name = "/tmp/aqdb_schema.png", *args, **kwargs):
    ios = cStringIO.StringIO(create_schema_graph(metadata=db.meta).create_png())
    Image.open(ios).save(image_name)

def _render_table_record(table, metadata, show_indexes, show_datatypes):
    def format_col_type(col):
        try:
            return col.type.get_col_spec()
        except NotImplementedError:
            return str(col.type)

    cols = list()
    for col in table.columns:
        str="- %s" % (col.name)
        if show_datatypes:
            str = "%s : %s"%(str, format_col_type(col))
        cols.append(str)

    text="\"{%s|%s}\"" % (table.name, "\\l".join(cols))
    return text


def _mk_label(mapper, show_operations, show_attributes,
              show_datatypes, bordersize):
#TODO: use template strings for these
    html = '''
<<TABLE CELLSPACING="0" CELLPADDING="1" BORDER="0" CELLBORDER="%s" ALIGN="LEFT"
><TR><TD><FONT POINT-SIZE="10">%s</FONT></TD></TR>'''%(
        bordersize, mapper.class_.__name__)

    def format_col(col):
        colstr = '+%s' % (col.name)
        if show_datatypes:
            colstr += ' : %s' % (col.type.__class__.__name__)
        return colstr

    if show_attributes:
        html += '<TR><TD ALIGN="LEFT">%s</TD></TR>' % '<BR ALIGN="LEFT"/>'.join(
                    format_col(col) for col in sorted(
                        mapper.columns, key=lambda col:not col.primary_key))
    else:
        [format_col(col) for col in sorted(
            mapper.columns, key=lambda col:not col.primary_key)]
    if show_operations:
        html += '<TR><TD ALIGN="LEFT">%s</TD></TR>'%'<BR ALIGN="LEFT"/>'.join(
            '%s(%s)' % (name,", ".join(default is _mk_label and (
                "%s") % arg or (
                "%s=%s" % (arg,repr(default))) for default,arg in zip(
                (func.func_defaults and len(func.func_code.co_varnames)-1-(
                    len(func.func_defaults) or 0) or
                 func.func_code.co_argcount-1)*[_mk_label]+list(
                    func.func_defaults or []),
                func.func_code.co_varnames[1:]))) for name, func in
            mapper.class_.__dict__.items() if isinstance(
                func, types.FunctionType) and
        func.__module__ == mapper.class_.__module__)
    html+= '</TABLE>>'
    return html


""" from aquilon.aqdb.utils.schema2dot import create_schema_graph,
                                           create_uml_graph,
                                           show_schema_graph,
                                           show_uml_graph)
def write_uml_graph(db, image_name = "aqdb_classes.dot"):
    Base.metadata = db.meta
    graph = create_uml_graph(
              [class_mapper(c) for c in Base._decl_class_registry.itervalues()])
    graph.write_dot(name)
"""
