# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2013  Contributor
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
                # note: we shouldn't have any trailers!
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
