# Aquilon

The instruction below describes how to install Aquilon from the sources and run it as a non-root user. The
installation steps described here require that you are root on the machine. It is possible to do the
installation itself as an ordinary user, using a Python virtualenv, but this is not described here (if
you need it, you are assumed to know what is involved in setting a virtualenv environment).

*Note: the commands provided in this documentation are intended to be copy/pasted.*

## Install Dependencies

Add EPEL repository.

Under EL7, you need to install RPMs listed below. For this you need to have the following YUM repository
configured:
* OS YUM repository
* EPEL7
* [Quattor EL7 x86_64 externals](http://yum.quattor.org/externals/x86_64/el7/)
* [Quattor EL7 noarch externals](http://yum.quattor.org/externals/noarch/el7/)

RPMS to install are:

```bash
yum install python python-devel python-setuptools python-dateutil python-lxml python-psycopg2 \
  python-coverage python-ipaddr python-mako python-jsonschema PyYAML python-cdb python-twisted-runner \
  python-twisted-web ant-apache-regexp ant-contrib-1.0 gcc protobuf-compiler protobuf-python \
  make git git-daemon libxslt-devel libxml2-devel java-1.8.0-openjdk-devel panc \
  knc krb5-workstation python-pip
# If you don't use an external Kerberos server
yum install krb5-server
```

In addition install the `sqlalchemy` module from PIP (the EPEL version is too old):

```bash
pip install sqlalchemy
```

If using a distribution other than EL7, you will need python 2.7.x and git
1.7+.

* protobuf
* protobuf-devel
* protobuf-compiler
* protobuf-python


## Cloning the git repositories


Protocols:

```bash
cd your_work_directory
git clone https://github.com/quattor/aquilon-protocols.git
```

Pass in an alternate INSTALLDIR if desired.  Compiling the protocol
buffers into perl may fail.

```bash
cd aquilon-protocols
make PROTOC=protoc install
# or
make INSTALLDIR=/usr/local/lib/aquilon/protocols PROTOC=protoc install
```
Aquilon itself:

```bash
cd /opt/
git clone https://github.com/quattor/aquilon.git
```

## Installation

If the installation is done as root and all the dependencies (listed in `/opt/aquilon/setup.py` have been installed
as RPM or using the `pip` command, there are no more installation steps to do and you should be able to run the
`/opt/aquilon/tests/dev_aqd.sh`. This command should fail with:

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
```

Any other error means that something is wrong in the installation

### Installation as a non-root user

**This section is for advanced users only.**

If you install Aquilon in a Python virtualenv, you need to run the following commands to get the
dependencies into your virtualenv.

```bash
cd aquilon/tools
./bootstrap_env.py > aq_env.py
aq_env.py --python=python2.7 --prompt="(aquilon) " /usr/local/aquilon/pythonenv --system-site-packages
```

Note:

 * The `cx_Oracle` install will fail if there is no local Oracle client installed - that's fine.
 * `cdb` package installed as a RPM will be reported as missing but it should not prevent the installation from working
 * For some packages, the current stable version may be used instead of the minimum requested version

If the installation succeeded, the following directories should be present: `/usr/local/aquilon/pythonenv`
and `/usr/local/bin/aquilon`.

To add the Aquilon dependencies to Python path, execute:
```bash
source /usr/local/aquilon/pythonenv/bin/activate
```

## Broker Configuration


### Create the Broker Configuration

Setup up the aquilon broker configuration file.  There is an example
in `/opt/aquilon/etc/aqd.conf.defaults`.  Move this file to `/etc/aqd.conf`
and create a empty `/opt/aquilon/etc/aqd.conf.defaults` file
(or define the `AQDCONF` environment variable to point wherever it is
installed). The default will use a sqlite database back-end. Main required
changes are:

* `dsdb`: change to `/bin/true`
* `git_daemon`: change to `/usr/libexec/git-core/git-daemon`
* `ant_contrib_jar`: change to `/usr/share/java/ant/ant-contrib.jar`
* Comment out every else in the `tool_locations` section that point to a path
starting with `/ms`
* `pan_compiler`: change to `/usr/lib/panc.jar`
* `directory`(in `protocols`section): change to `/usr/local/lib/aquilon/protocols/lib/python`


### Configure the Kerberos Server

If you don't rely on an existing Kerberos server, you need to setup one. See the
following [instructions](http://tldp.org/HOWTO/Kerberos-Infrastructure-HOWTO/install.html).
In `/etc/krb5.conf`, change server to servername in [realms] section.*

*Note: if you install the Kerberos on a new machine with not a lot of activity, it may take
a while for the Kerberos database creation to complete, due to its need to wait for enough
randomness entropy. To speed up this process, you can follow the recipe at
http://championofcyrodiil.blogspot.fr/2014/01/increasing-entropy-in-vm-for-kerberos.html.*

Be sure to define properly the domain associated with your realm: it must match your actual
domain.

If you don't run as `root`, be sure to create a keytab for the current user.

### Create a User to Run the Broker

It is recommended not to run the broker as root. This cause quite a number of problem with
Kerberos in particular. To create and configure a user to run the broker:

```bash
adduser aquilon
mkdir /var/spool/keytabs
kadmin.local
kadmin.local: addprinc aquilon
kadmin.local: addprinc aquilon/your.host.fqdn
kadmin.local: ktadd -k /var/spool/keytabs/aquilon
kadmin.local: quit
chown aquilon:aquilon /var/spool/keytabs/aquilon
```

### Initialize the Aquilon Database

To create the Aquilon database:

```bash
mkdir -p /var/quattor/aquilondb
chown -R aquilon:aquilon /var/quattor
su - aquilon
kinit        # Enter the password you set previously
/opt/aquilon/tests/aqdb/build_db.py
```

### Test The Broker

To test the broker, run `/opt/aquilon/tests/dev_aqd.sh` that must run successfully if your
installation is correct. Before running this script, you need to define `AQDCONF` environment
variable to `/etc/aqd.conf` (the script uses `/etc/aqd.conf.dev` by default).

To check that the broker is working properly, in another window, execute the
following command:

```bash
/opt/aquilon/bin/aq.py status
```

The command should return some information on your current Aquilon environment, without any error.
If this is the case, stop the broker started by the `dev_aqd.sh` script.


### Start the Production Broker

Starting the production service:

* Edit `/opt/aquilon/etc/rc.d/init.d/aqd` and add the following lines if they are not present

```
# chkconfig: 2345 99 1
# description: Aquilon Broker
```

* Edit `/opt/aquilon/etc/sysconfig/aqd` and change `TWISTD` to `/opt/aquilon/sbin/aqd.py`
* Create `/var/log/aquilon` and set the owner to `aquilon:aquilon`
* Create `/var/run/aquilon` and set the owner to `aquilon:aquilon`
* Configure the init script and start the service
```bash
ln -s /opt/aquilon/etc/rc.d/init.d/aqd /etc/init.d
chkconfig --add aqd
ln -s /opt/aquilon/etc/sysconfig/aqd /etc/sysconfig
service aqd start
```

### Git Daemon Configuration

Create a bare Git repository in /var/quattor/template-king that will be the master repository for
the templates and create its `prod` branch (which is expected to exist after the database
initialization but is not created):

```bash
git init --bare /var/quattor/template-king
cd /tmp
git clone /var/quattor/template-king
cd template-king
touch README.md      # You may want to add something in it but this is not required
git add README.md
# If Git complains about missing user.email and user.name, define them (actual value does not matter)
git commit -am 'Empty README added'
git push origin master:prod
```

Then start the Git daemon:

```bash
git daemon --export-all --base-path=/var /var/quattor/template-king/ &
```

## Aquilon DB Configuration

See http://www.quattor.org/documentation/2013/10/25/aquilon-site.html