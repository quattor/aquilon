# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon


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
                line = line[:i] # strip chunk-extensions
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


