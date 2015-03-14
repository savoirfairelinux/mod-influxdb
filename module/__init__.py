"""
Shinken mod-InfluxDB Module.
"""

from .module import InfluxdbBroker
from shinken.log import logger

properties = {
    'daemons': ['broker'],
    'type': 'influxdb_perfdata',
    'external': False,
}


# Called by the plugin manager to get a broker
def get_instance(mod_conf):
    logger.info(
        "[influxdb broker] Get an influxdb data module for plugin %s"
        % mod_conf.get_name()
    )
    instance = InfluxdbBroker(mod_conf)
    return instance
