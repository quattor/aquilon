# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import ms.version
import ms.modulecmd

ms.modulecmd.load('fsf/libtool/1.5.18')
ms.modulecmd.load('fsf/graphviz/2.24.0')

ms.version.addpkg('pyparsing', '1.5.5')  # pydot relies on pyparsing
ms.version.addpkg('pydot', '1.0.2')
import pydot

from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.properties import PropertyLoader

from aquilon.aqdb.model import Base


def create_uml_graph(mappers,
                     show_attributes=True,
                     show_multiplicity_one=False,
                     show_datatypes=True,
                     linewidth="1.0",
                     font="Sans-Serif"):

    graph = pydot.Dot(prog='neato', mode="major", overlap="0", sep="0.01",
                      pack="True", dim="3", concentrate="True", rankdir="TB")
    relations = set()

    for mapper in mappers:
        graph.add_node(
            pydot.Node(mapper.class_.__name__,
                       #shape="plaintext",
                       shape="record",
                       label=_mk_label(mapper, show_attributes, show_datatypes),
                       #label = mapper.class_.__name__,
                       fontname=font, fontsize="8.0"))

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

            def calc_label(src, dest):
                return '+' + src.key + multiplicity_indicator(src)
            args['headlabel'] = calc_label(src, dest)
            args['taillabel'] = calc_label(dest, src)
            args['arrowtail'] = 'none'
            args['arrowhead'] = 'none'
            args['constraint'] = False
        else:
            prop, = relation
            from_name = prop.parent.class_.__name__
            to_name = prop.mapper.class_.__name__
            args['headlabel'] = '%s%s' % (prop.key,
                                          multiplicity_indicator(prop))
            args['arrowtail'] = 'none'
            args['arrowhead'] = 'vee'

        graph.add_edge(
            pydot.Edge(from_name, to_name, fontname=font, fontsize="7.0",
                       style="setlinewidth(%s)" % linewidth,
                       arrowsize=linewidth, **args))

    return graph


def create_schema_graph(tables=None, metadata=None, show_datatypes=False,
                        font="Sans-Serif", concentrate="True",
                        relation_options=None, rankdir='TB'):
    relation_options = {}
    relation_kwargs = {'fontsize': "7.0"}
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
                      concentrate=concentrate, rankdir=rankdir, font=font,
                      fontsize="7.0")

    #Grossly inefficient. We can do this once for the whole graph
    for table in tables:
        graph.add_node(pydot.Node(str(table.name), shape="record",
            label=_render_table_record(table, show_datatypes)))

    for table in tables:
        for fk in table.foreign_keys:
            edge = [table.name, fk.column.table.name]
            is_inheritance = fk.parent.primary_key and fk.column.primary_key
            if is_inheritance:
                edge = edge[::-1]
            graph_edge = pydot.Edge(
                headlabel=" %s" % fk.column.name,
                taillabel=" %s" % fk.parent.name,
                arrowhead=is_inheritance and 'inv' or 'normal',
                arrowtail=(fk.parent.primary_key or
                           fk.parent.unique) and 'empty' or 'crow',
                *edge, **relation_kwargs)

            graph_edge.set_parent_graph(graph.get_parent_graph)
            graph.add_edge(graph_edge)
    return graph


def write_schema_dot(meta, file_name='/tmp/aqdb_schema.dot'):
    create_schema_graph(metadata=meta).write(file_name)


def write_uml_png(file_name='/tmp/aqdb_uml.png'):
    r = Base._decl_class_registry
    g = create_uml_graph([class_mapper(c) for c in r.itervalues()])
    g.write_png(file_name)


def write_schema_png(meta, file_name="/tmp/aqdb_schema.png"):
    create_schema_graph(metadata=meta).write_png(file_name)


def _render_table_record(table, show_datatypes=False):
    def format_col_type(col):
        try:
            return '%s' % col.type.__class__.__name__.title()
        except NotImplementedError:
            return str(col.type).title()

    cols = list()
    for col in table.columns:
        if col.name in ['id', 'creation_date', 'comments']:  # skip these columns
            continue
        desc = "%s" % (col.name)
        if show_datatypes:
            label = "%s : %s" % (desc, format_col_type(col))
            cols.append(label)
        else:
            cols.append(desc)
    if len(cols) == 0:
        return "\"{%s}\"" % table.name.title()
    else:
        return "\"{%s|%s\l}\"" % (table.name.title(), "\\l".join(cols))


def _mk_label(mapper, show_attributes=True, show_datatypes=True):

    def format_col(col):
        colstr = "%s" % (col.name)
        if show_datatypes:
            ''.join([colstr, " : %s" % (col.type.__class__.__name__)])
        return colstr

    attrs = list()
    if show_attributes:
        desc = '\\l'.join(format_col(col) for col in
                          sorted(mapper.columns,
                                 key=lambda col: not col.primary_key))
        attrs.append(desc)

    else:
        #WARNING: untested
        attrs = [format_col(col) for col in sorted(
            mapper.columns, key=lambda col:not col.primary_key)]

    return "\"{%s|%s}\"" % (mapper.class_.__name__, "\\l".join(attrs))
