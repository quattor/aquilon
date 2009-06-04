# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
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
