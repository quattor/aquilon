Troubleshooting
===============

If you see a line like the following:

    Error: BadStatusLine('',): knc[13217]: gstd_error: gss_init_sec_context: Server not found in Kerberos database

Set AQSERVICE to match the service name in the keytab that aqd is
running with, eg:

    export AQSERVICE=http

Bug Reporting
-------------

Aquilon, like all software, contains bugs. If the problem your
experiencing looks to be misbehavior by the compiler, please report the
problem. Bug reports can be filed in the in the issues area of GitHub.

    https://github.com/quattor/aquilon/issues

