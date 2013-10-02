Aquilon Primer
==============

Aquilon[^1] is a configuration system that manages operating system
level configuration and installation of hosts. The hosts managed by
Aquilon can be Linux hosts, CISCO switches, NetApp filers or almost
anything else. As of September 2009, Linux and VMware builds are
supported; NetApp filers are under development.

For the host being managed by Aquilon, there is an operating environment
that takes advantage of the Aquilon configuration system and presents
features to the client application. For example, we provide a Linux
build based on Red Hat’s enterprise distribution. This Linux environment
presents features such as Lemon monitoring. This Linux build is also
named Aquilon. Other managed hosts may have alternately named builds.

Aquilon is a management layer that sits above Quattor[^2]; all the
standard Quattor toolset is used within Aquilon.

## Features

-   Simple configuration changes are immediately applied. For a grid
    of 15,000 machines "immediate" means within approximately 20
    minutes.

-   You can customize any part of the system from the personality. This
    means that applications can dictate RPMs to install, turn off swap
    devices, etc. Integrated configuration allows such changes to be
    correctly reflected in monitoring configuration. For example, we
    don’t setup monitoring of swap if the host does not have any swap.

-   Configuration is consistently applied across the plant. If DNS
    servers change, subscribers automatically update their configuration
    "instantly". Reconfiguration in such cases is also directed: only
    the managed hosts that were using that service would be updated.
    Such configuration is managed directly by commands from the Aquilon
    broker.

-   The modeling of distributed services provides rudimentary capacity
    planning of the infrastructure across the plant and explicit
    descriptions of how services are deployed.

-   Configuration is prescribed by the application. For example, login
    access to hosts is dictated by who needs access to meet the
    objectives of the application, and is not a simple generalization
    across the entire global plant.

-   Configuration is entirely known and modeled before being applied to
    a host. This means that configuration can be validated for
    consistency at the plant level rather than calculated at runtime on
    the host under management. This means that the CMDB contains
    information known to be correct instead of inferring CMDB
    information by later analysis.

-   A hierarchical location model allowing location-specific attributes
    to be easily specified.

## Quattor

Aquilon is based on Quattor. So, what features and limitations does that
present?

### What Quattor Provides Out-of-the-Box

Quattor provides two core systems: the template system and the build
infrastructure. Any kernel parameters (i.e. sysctl settings). This
includes such things as shared and virtual memory configuration, and
TCP-IP tunables.

-   The template system provides: a rich template language (known as
    Pan) that includes configuration validation; a large template
    library describing grid configuration; a model to describe a machine
    configuration.

-   The compile and build and application infrastructure provides: DHCP
    configuration allowing machines to be automatically installed;
    datawarehouse facilities to present expected host configuration;
    component code that can control most of the configurable aspects of
    Linux and can affect changes almost instantly.

These two systems are loosely coupled. The template compiler can be used
to generate XML profiles independently of any other Quattor system.

The list of elements of configuration that can be controlled by Quattor
is almost unlimited. Out-of-the-box, Quattor has specific support for:

-   What RPM packages should be installed on a host, including support
    for vendor-supplied operating system errata.

-   Directory layouts, files and symbolic links that should exist on the
    host.

-   Any kernel parameters (i.e. sysctl settings). This includes such
    things as shared and virtual memory configuration, and TCP-IP
    tunables.

-   Configuration of any system service: how to start system daemons,
    what configuration they should use.

-   Monitoring: what agents to install on the host, how and what they
    should be monitoring.

-   User access to the machine: who has login privileges (by way of PAM
    configuration).

-   Password control such as root password distribution.

-   Much more including specialized configuration for iptables,
    networking, http servers, NFS services, etc.

### What Quattor Does Not Provide

-   No data model except that provided within the templates language
    itself and except by the validation supplied by the user. This means
    that relationships between hosts are awkward to describe and prone
    to error.

-   No entitlements or delegation model are provided by Quattor. The
    Quattor community recognize this as a problem, although not with a
    high priority.

-   No feedback mechanism for validating the real application of a
    configuration compared to the expected configuration. This is not
    considered to be a problem by the Quattor community; configuration
    is either completely correct (an overall failure can be moni-
    tored), or is reapplied. Partial configuration is not allowed or
    catered for.

## Aquilon

### What Aquilon Provides

The layer of management provided by Aquilon includes:

-   A relational data model (AQDB) that describes the overall plant.

-   An entitlement model that restricts access to functionality. This is
    a simplistic role-based modeling in the early releases, but future
    releases may provide more complex entitlement rules.

-   A broker model that packages common template tasks into commands
    that can be delegated to users who have no knowledge of the Pan
    language.

-   Broker tasks that scan for new hardware and provides automation of
    host installation.

### Monitoring

The Linux build of Aquilon provides monitoring by way of the Lemon
system. Lemon configuration is fully integrated with Quattor which means
that the specific pieces to monitor are defined by template and
personality. The Lemon agents that run on the managed host are installed
with RPMs. Lemon provides metrics, sensors, exceptions and actuators.

-   Metrics are the data being measured. Defining new metrics requires
    modifying the Lemon database schema.

-   Sensors are code that retrieves metrics to provide to the Lemon
    agent. Sensors are written in either perl or C. There are generic
    sensors supplied with the product that allow measuring of a wide
    range of metrics including tracking messages in logfiles, watching
    processes, etc.

-   Exceptions are conditions that are tested on the local host. The
    conditions can be arbitrarily complex and encompass any metric. If
    an exception is triggered, it appears as a special metric within
    Lemon (i.e. available for reporting).

-   Actuators are agents that run on a local host when an exception has
    been detected. Actuators are arbitrary command lines and are
    intended to be commands that try to fix the problem. If the actuator
    can fix the problem, then the exception is not reported to Lemon.
    The configuration says how many times an actuator should be
    attempted before deciding that the exception is worth reporting to
    the Lemon server.

### Hidden Features

Quattor and Aquilon provide a large amount of functionality, not all of
which is currently presented within our interfaces. This list describes
features that are possible with the current implementation, but may not
be exposed in day-to-day usage:

1.  The system is designed to manage the underlying host operating
    system. Although the configuration of the host is prescribed by the
    application, the system is not designed to configure the
    applications themselves. That said, there’s nothing in the system
    preventing such usage and there are benefits to doing so (the same
    benefits that drove the usage of Quattor for infrastructure). No
    effort has been made to develop this possibility, since the runtime
    configuration is typically already managed by more domain-specific
    tooling.

2.  The Aquilon/Linux build installs the operating system locally. If an
    application wants to run their application from the local disk, they
    can provide a RPM and this will work as expected. No dependency
    management or tooling is provided to assist in such a configuration
    and there are some unresolved issues around tracking software in use
    and dependency conflicts. Extreme differences in configuration will
    cause an impact on the supportability of Aquilon managed hosts. If a
    host has different RPM installations to “the norm”, then system
    administrators lose many of the advantages arising from homogenous
    environments: every outage investigation must begin with discovering
    the configuration of the host. This problem increases with the
    number of variations in host profiles: every new personality adds to
    the support burden.

3.  Quattor understands having two profiles available on a host: a
    profile and a “context”. The context is an additional XML document
    that can be downloaded from a completely different from where the
    profile was sourced. The context and the profile are merged to
    provide a final profile for the host. This has two possible
    applications:

    1.  Making the system more efficient. There is typically 200KB of
        data in the profile that is standard between all other hosts in
        the profile. That common data could be factored into a common
        context and shared between all hosts with the same hardware,
        usage and personality. Such a factorization could produce
        dramatically faster compilation, validation and distribution of
        profiles.

    2.  Allowing “devolved” administration. The profile could be managed
        by a central asset database, while more local administration
        retain complete control of passwords, access-control and the
        like by storing such information in the host context and
        providing a merge function that prioritizes the local context
        over the host’s centrally generated profile. The devolved
        management model is currently used by a number of organizations
        using Quattor and is described in the 2008 LISA paper.

        The downside to this system is that the validation of the host
        profile has less meaning: validation should instead be applied
        to the context and profile merge, however this is not possible.

4.  Aquilon provides a mechanism, called “tellme”, for distribution of
    secrets7. This is typically used for distributing a common root
    password crypt to a group of hosts, however this allows arbitrary
    secrets to be distributed and could be used by other infrastructure
    applications.

5.  Lemon exceptions and actuators are very extensible and allow for
    automating many common fixes. Possibilities include deleting old
    files, restarting processes, rebooting or even reinstalling hosts.
    Lemon could replace sysedge, kiwa, checkout and harvester.

6.  The Aquilon system allows arbitrary hosts to be managed.
    Configuration profiles can be generated for any type of host,
    including Windows hosts, network switches and NetApp filers. We can
    provide a compiled, validated profile for almost any device.

### Deployment Requirements

To deploy a single Aquilon managed host the following pieces of
infrastructure are necessary:

1.  A database providing the Aquilon data model. This is currently an
    Oracle database, but we expect to be able to move to other databases
    easily.

2.  A broker that takes user requests and combines database information
    with configuration policy to produce host profiles.

3.  A datawarehouse process. This typically runs on the Aquilon host.
    The job of the datawarehouse process is to export realized views of
    the Aquilon data model into a form that can be consumed easily, at
    scale, and under BCP conditions.

4.  A bootserver that transforms host profiles into configuration that
    allows network installation. A bootserver is required to reinstall a
    host and typically would be configured in pairs to provide a small
    measure of fault tolerance.

5.  Networking configuration will need to be modified to point iphelpers
    at the Aquilon bootservers in addition to the standard Aurora
    bootserver.

6.  A DNS server providing the new Aquilon-ready view of the DNS
    namespace.

The database, broker and datawarehouse process can all be located
centrally and used by clients in any location. The core systems are
required to affect any changes but are not involved in the runtime
booting of hosts. The bootserver must be available through a network
local to the managed host. Typical installations will have numerous boot
servers located in every data center, with a single centralized database
and broker.

If configuration is being managed by Quattor that does not require a
bootserver (for example, providing profiles for NetApp filers), then the
bootserver deployment is unnecessary: compiled profiles can be retrieved
directly from the broker and the datawarehouse.

### Modifying Aquilon

#### Summary

The system directly supports creating new operating system builds, or
new styles of host. Such changes can be done using normal broker
commands and by writing and submitting new templates into the library.
Such tasks are typically measured in days or weeks.

Changing the data model requires a schema and a broker upgrade. Such
tasks are typically measured in many weeks.

A breakdown of some typical activities are shown, giving an idea of how
much effort is required to create new functionality.

#### New Configuration Components

To be able to change some part of a host’s configuration not currently
implemented by Aquilon, but on a host which is managed by Aquilon, a new
component must be created. Components are dynamically loaded and require
no upgrade to broker or data model. The following tasks are required:

1.  Write the new component to affect the configuration. This requires
    perl skill and a small amount of Pan knowledge. This typically takes
    about a week. If the necessary host change is simple and supported
    by the existing template library, then this step can be skipped.

2.  Modify the archetype within the provided template libraries to
    describe when it is applicable to invoke the new configuration
    component. This can be implemented within a day by someone with
    knowledge of Pan and the template library. Low-level changes to the
    library would still require full testing procedures that typically
    require a week.

#### Adding a New Style of Managed Host

To add a new managed type into Aquilon (for example, a NetApp filer),
the following pieces of work may be required:

1.  (Optional) Describe the hardware layout in the database. For typical
    compute based hardware, this simply requires someone with
    engineering privileges that can run the relevant few commands. If
    the hardware needs to be modeled differently, then schema may need
    to be modified within the database. Such schema modifications are
    usually simple subclassing and therefore require minimal time to
    complete, but require Data modeling experience; python and
    SQLAlchemy experience.

2.  Describe an "archetype" to Aquilon. The archetype describes the
    build and management process of the managed host, and is described
    within templates. Writing (or copying) skeleton templates takes
    little time, and requires facility with the PAN template language.
    The archetype includes operating system templates which may be
    copied from other archetypes that share similar operating systems.
    The broker provides commands to facilitate the creation of new
    archetypes.

3.  Implement configuration components that take compiled profiles and
    applies the configuration to the managed host. There are two
    frameworks to ease this: the original Quattor "Node Configuration
    Dispatcher" which runs on the managed host itself and would require
    porting to any new operating system; or the quattor-remote-configure
    facility provided by Aquilon which requires a connector API to cause
    configuration changes to happen remotely. Both systems provide a
    framework for deciding what component configuration to run. The code
    of the individual configuration components must be written by the an
    integrator and is probably the most intensive part of the work. This
    requires knowledge of how the components are executed and Perl
    skills. Several weeks should be set aside for this task.

4.  Developing and fleshing out the templates that describe host
    configuration policy. This requires PAN language skills. This step
    is the “interesting” part and can take many weeks, typically in
    parallel with step 3.

#### Adding New Management Paradigms

To add a new management paradigm into Aquilon (for example, a new way of
clustering hosts together), the following tasks may be required:

1.  New commands must be implemented that cause the desired effects. New
    broker commands are typically fairly quick to implement. This
    requires python programming and knowledge of the AQD broker and
    schema. Expect a couple of weeks for this task.

2.  New schema within the data model that expresses the desired
    configuration. If the schema change is a simple extension of the
    existing model, then it will be simple and quick to implement.
    However, when creating brand new schema, this task is the most
    intensive and can require a number of iterations to ensure a correct
    interaction with existing schema. Each iteration needs to be worked
    in conjunction with the implementation of the new commands. This
    requires facility with database modeling; knowledge of the AQD
    schema; python and SQLAlchemy skills. Expect many weeks for this
    task.

3.  It might be necessary to expose the new configuration by way of
    datawarehouse methods. This typically takes a couple of weeks and
    requires knowledge of the access methods for the existing
    datawarehouse; Perl skills.

4.  It may be necessary to implement new configuration components as
    part of the task. This is described previously.

#### Extending the Data Model

Sometimes adding new functionality in the configuration of a managed
host will best be implemented by accessing data from AQDB but with data
which is not currently stored in the data model. This route (as opposed
to putting data into templates) should be followed when the data
requires relational integrity.

1.  Decide if the data should be canonically homed within AQDB, or is
    better managed externally. If the data will be external, then import
    methods must be created within the broker. If the data will be homed
    in AQDB, then methods to bootstrap the population of the data must
    be designed.

2.  Design the new schema additions including the typical queries for
    accessing the data. This requires data modeling experience,
    knowledge of python and SQLAlchemy. This can take a few weeks.

3.  Implement either the import command or new commands for managing the
    data canonically via the broker. This will typically be a quick
    process once the schema has been completed. If the data is to be
    managed by import, then Autosys should be used to trigger the import
    on an appropriate schedule. This task requires python knowledge and
    typically takes a week or two.


[^1]: Aquilon is based on the Roman name for the god of the North Wind.
    In mythology, Aquilon was the son of Aurora.

[^2]: Quattor is an open-source product originally developed at CERN and
    now maintained by a consortium of users known as the Quattor Working
    Group (QWG).
