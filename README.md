Aquilon
=======

Dependencies
------------

Add EPEL repository.

Under Scientific Linux 7, install the following RPMs:

*   python
*   python-devel
*   python-setuptools
*   python-dateutil
*   python-cdb
*   python-lxml
*   python-virtualenv
*   PyYAML
*   protobuf-compiler (to build the protocol buffers)
*   protobuf-python
*   gcc
*   git
*   git-daemon
*   ant-contrib-1.0
*   make

* real version of java (not GCJ!); openjdk?, oracle?

Kerberos

* krb5-server
* krb5-workstation

See instructions for [krb5
installation](http://tldp.org/HOWTO/Kerberos-Infrastructure-HOWTO/install.html). In
/etc/krb5.conf, change server to servername in [realms] section.


If using a different distribution, you will need python 2.7.x and git
1.7.x.

* protobuf
* protobuf-devel
* protobuf-compiler
* protobuf-python

Install the knc package from the
[Quattor repository](http://yum.quattor.org/external), or build your own from
sources at http://oskt.secure-endpoints.com/knc.html
```bash
easy_install virtualenv
```


Cloning the git repositories
----------------------------

Protocols:

```bash
cd ~
git clone git://quattor.git.sourceforge.net/gitroot/quattor/protocols
```

Pass in an alternate INSTALLDIR if desired.  Compiling the protocol
buffers into perl may fail.

```bash
make PROTOC=protoc install
# or
make INSTALLDIR=/usr/local/lib/aquilon/protocols PROTOC=protoc install
```
Aquilon itself:

```bash
cd /opt/
git clone git://quattor.git.sourceforge.net/gitroot/quattor/aquilon
```

Installation
------------

Run as root to install to a system directory, or run as a normal user
to install into a user-writable location.

```bash
cd tools
./bootstrap_env.py > aq_env.py
```

The `cx_Oracle` install will fail if there is no local Oracle client
installed - that's fine.  Some versions may fail to install, and the
current stable version will be installed instead.

```bash
python2.7 aq_env.py --python=python2.7 --prompt="(aquilon) " /usr/local/aquilon/pythonenv --system-site-packages
```

(look in following for installed files
 `/usr/local/aquilon/pythonenv`
 `/opt/aquilon`
 `/usr/local/bin/aquilon`)

An environment has now been setup appropriate for running commands and development.

To activate the environment:

```bash
source /usr/local/aquilon/pythonenv/bin/activate
```

Alternately, just add the bin directory to the $PATH.


Configuration
-------------

Setup up the aquilon broker configuration file.  There is an example
in etc/aqd.conf.example.com.  Copy that to the system /etc/aqd.conf or
just set the `AQDCONF` environment variable to point wherever it is
installed.  Update the file as needed. The default will use a sqlite
database back-end.

(change configuration from `database_oracle` to `database_sqlite`)

(add directories `/var/quattor` `/var/quattor/logs` `/var/quattor/aquilondb`)

Take a look at the example load file for the database in the aquilon
source repository's tests/aqdb/example.dump.  Update as desired for
the site.  When ready, a database can be initialized (or recreated)
with the following command.

Set up AQDCONF (or have an /etc/aqd.conf) as described above first.
Create the database directory if using sqlite and it does not exist.

```bash
cd ../tests/aqdb
./build_db.py -D
```

(ignore warning on administration not setup)

Make sure there is a keytab set up for the running user, and then
try starting up a development broker:

(add to configuration file /etc/aqd.conf:

```ini
[protocols]
directory=/usr/local/lib/aquilon/protocols/lib/python
```

and

```bash
export AQDCONF=/etc/aqd.conf
```
)


(change aqd.conf.defaults in aquilon install etc area)

```bash
cd ..
./dev_aqd.sh
```

In another window:

```bash
cd aqd/bin
AQSERVICE=$USER ./aq.py status
```

To test without kerberos:

```bash
./aq.py status --noauth
```

Misc. Bits
----------

```bash
chmod a+x     /usr/local/aquilon/pythonenv/bin/activate
```
source this instead...

Need to create a kerberos keytab...

change service `AQSERVICE`:

```bash
export AQSERVICE=aqd
export AQDCONF=/etc/aqd.conf
```

Setup bare git repository in /var/quattor/template-king.

in aqd.conf.defaults, change:

```ini
dsdb = /bin/echo
dsdb_use_testdb = True
```


# starting git

```bash
git daemon --export-all --base-path=/var /var/quattor/template-king/ &
```

# production service...

```bash
python2.7 /opt/aquilon/bin/twistd.py --logfile=/var/log/aqd.log aqd
```
