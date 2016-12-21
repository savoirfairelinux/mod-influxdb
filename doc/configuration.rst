=============
Configuration
=============

Shinken InfluxDB module
=======================

influxdb.cfg 
------------

::

    ## Module:      mod-influxdb
    ## Loaded by:   Broker
    # Export host and service performance data and events to InfluxDB.
    # InfluxDB is an open-source distributed time series database with no external
    # dependencies. http://influxdb.com/
    define module {
        module_name     influxdb
        module_type     influxdb_perfdata
        host            localhost
        port            8086
        user            root
        password        root
        database        shinken
        #use_udp        1 ; default value is 0, 1 to use udp
        udp_port        4444
        #tick_limit     300 ; Default value 300
    }

Parameters details
~~~~~~~~~~~~~~~~~~

:host: 
:port: 
:user:
:password:
:database:
:use_udp:
:udp_port:
:tick_limit:

Custom tag for hosts and services
---------------------------------

You can use the macro _INFLUX_TAG inside your services or your host to add a custom tag.
A custom tag with tag key ``T1``, value ``V1`` is write ``T1:V1``
You can add different tag using ``,``

::

    # Exemple
    _INFLUX_TAG T1:V1,T2:V2
