# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010  Contributor
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


import httplib


class ChunkedHTTPResponse(httplib.HTTPResponse):
    # This is a modification on the stock _read_chunked() to return
    # chunks as we get them.
    def read_chunk(self, amt=None):
        if self.fp is None:
            return ''

        if not self.chunked:
            return self.read(amt)

        chunk_left = self.chunk_left
        value = ''

        if chunk_left is None:
            line = self.fp.readline()
            i = line.find(';')
            if i >= 0:
                line = line[:i]  # strip chunk-extensions
            chunk_left = int(line, 16)
            if chunk_left == 0:
                # read and discard trailer up to the CRLF terminator
                ### note: we shouldn't have any trailers!
                while True:
                    line = self.fp.readline()
                    if not line:
                        # a vanishingly small number of sites EOF without
                        # sending the trailer
                        break
                    if line == '\r\n':
                        break

                # we read everything; close the "file"
                self.close()

                return value
        if amt is None:
            value += self._safe_read(chunk_left)
        elif amt < chunk_left:
            value += self._safe_read(amt)
            self.chunk_left = chunk_left - amt
            return value
        elif amt == chunk_left:
            value += self._safe_read(amt)
            self._safe_read(2)  # toss the CRLF at the end of the chunk
            self.chunk_left = None
            return value
        else:
            value += self._safe_read(chunk_left)
            amt -= chunk_left

        # we read the whole chunk, get another next time
        self._safe_read(2)      # toss the CRLF at the end of the chunk
        return value


class ChunkedHTTPConnection(httplib.HTTPConnection):

    response_class = ChunkedHTTPResponse
