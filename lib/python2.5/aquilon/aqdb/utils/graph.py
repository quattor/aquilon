#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Database E/R and UML diagram generation based on SQLAlchemy code."""

from aquilon.aqdb.utils.sqlalchemy_schemadisplay import create_schema_graph, create_uml_graph

def write_schema_graph(base, name = "aqdb_schema.dot"):
    graph = create_schema_graph(metadata = base.metadata)
    graph.write_dot(name)

def write_uml_graph(base, name = "aqdb_classes.dot"):
    from sqlalchemy.orm import class_mapper
    graph = create_uml_graph([class_mapper(c) for c in base._decl_class_registry.itervalues()])
    graph.write_dot(name)
