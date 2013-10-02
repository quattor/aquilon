Getting Started
===============

Aquilon is the third generation configuration datastore for Quattor (The
1st generation being CDB and the 2nd being SCDB).

The biggest single change is the introduction of a broker daemon which
has overall ownership of the system including template compilation. The
broker stores specifc configuration in a relational database, generating
object templates on-the-fly at compile time.

All user interaction takes place over a kerberos secured connection to
the broker, which delegates sandboxes (taking the form of git
repositories) when changes to pan templates are needed.

Most operations do not require editing of templates and can be performed
in almost real-time with a single command, this opens the possibility
for event driven configuration changes and self modification by
configured systems.

Core Concepts
-------------

Basic terminology:

broker (aqd)
:   The backend which the aq client communicates with and the owner of
    all object and production templates.

sandbox
:   A working area owned by a specific user and associated with a group
    of systems.

archetype
:   The highest possible grouping of hosts into distinctly seperate
    types, analogous to a QWG site. Archetypes are a bundle that
    expresses how to build something. It defines what set of templates
    to use (for example, what operating systems are available, etc).
    Hosts therefore require an archetype to define how they are
    compiled.

domain
:   A high level grouping of hosts eg. prod

personality
:   Analogous to QWG machine types, describes the services required but
    not the instance (selected using plenary template information).

service
:   ...

feature
:   A chunk of code for configuring a specific thing, similar to Puppet
    recipes.

cluster
:   A group of hosts related in some way, different to an archetype in
    that hosts may or may not be in a cluster. When grouping hosts into
    a cluster, an object profile is also built for the cluster, as well
    as the hosts. Clusters go through a completely different schema and
    build process to how hosts are built and therefore have a different
    archetypes.

plenary
:   Equivalent of SCDB hardware/machine + the service/personality.
    Typically generated on the fly from an external source.

Installation
------------

There is an early version of a virtual appliance for trying out Aquilon,
available at http://sourceforge.net/projects/quattor/files/appliances/.
This version of the appliance is for testing only. Although it can
produce profiles, it is not yet integrated with QWG templates and there
is a large amount of work remaining to productionize the appliance.

This appliance provides: A complete quattor server distribution, managed
by Aquilon. This includes the 8.4 version of the PAN compiler.

-   A couchdb datawarehouse to describe all the profiles produced by the
    appliance.

-   A webserver providing access to the generated profiles and providing
    an interface to manage the appliance.

-   A couchdb datawarehouse to describe all the profiles produced by the
    appliance.

This virtual appliance is available in ISO format, tested with: VMware
Fusion on a Mac; and qemu/kvm under Fedora 15.

To install the appliance, create a Linux Ubuntu 64-bit VM (no special
requirements - I've typically used 5GB disk, 1GB memory, 1 processor)
with your favourite virtualization software. Add the ISO to the CD for
the virtual machine and boot the machine. On boot this will display a
Turnkey appliance logo and ask you to install the software on the
virtual machine. Please see the detailed appliance walkthrough if you
need more information.

Once the appliance has started up normally the console will show an
Aquilon URL that you can use from a web browser to activate the
appliance. You should see a web page similar to the screenshot below.

There is an intent to automate much of the activation but that work is
incomplete. Therefore the only option is to use ManualActivation manual
activation guide. This means you should fill in the organisation code
(the distinguished name in LDAP terms) and a text representation of the
organisation, but leave the Quattor URL empty. Submit that form to
activate your appliance. At this point your appliance will be ready for
use. You should be able to look at the appliance status, browse logs,
etc. Without any hosts defined within Aquilon, the datawarehouse will
not yet be of any use.

See the ManualActivation manual activation guide to continue setting up
your Aquilon appliance.

Appliance Walkthrough
---------------------

Creating an Aquilon appliance from the ISO should take only a couple of
minutes. Follow the steps below:

1.  At first you will see a Turnkey installation page offering to
    install to disk or run from the CD. Select "Install to disk" (the
    default) and press return.

2.  The next step will be to carve up the virtual disk into a useful
    form for the appliance. The easiest thing to do here is just to make
    the entire disk into a single logical partition and to install grub
    on that partition

3.  At this point the appliance will be installed and should be rebooted

4.  After the appliance boots it will ask for some passwords to be set.
    Please give some reasonable passwords for these accounts! These
    passwords are: root cdb (the identity under which all of the aquilon
    tools will run)

5.  TurnKey Linux provides "Hub services" which allows for a number of
    services related to the management of your appliance. If you have an
    API key for these services, you can enable them here. If you do not
    have an API key or you do not want to enable the service, then
    select Skip.

6.  You will be offered the chance to install security updates. You
    should select "Install".

7.  After the security updates have been applied (and it's possible that
    the machine may reboot here, but not always), the machine will
    present an information menu on the console which looks something
    like the below screenshot (your network addresses will probably be
    different to these!)

At this point your appliance is ready for use and you can follow the
regular Aquilon installation guide.
