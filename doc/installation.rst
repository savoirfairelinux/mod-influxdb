.. _collectd_installation:

============
Installation
============


Download
========

The InfluxDB module is available here: 
  * https://github.com/savoirfairelinux/mod-influxdb

Requirements
============

The InfluxDB module requires:

  * Python 2.6+
  * Shinken 2.4+
  * python-influxdb >=1.0.0
  * InfluxDB >= 0.9.0

Installation
============

Manual installation
~~~~~~~~~~~~~~~~~~~

Copy the InfluxDB module folder from the git repository to your shinken/modules directory (set by *modules_dir* in shinken.cfg)

CLI installation
~~~~~~~~~~~~~~~~

Run the following command: ``shinken install mod-influxdb``
  
