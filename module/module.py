#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# Copyright (C) 2014 - Savoir-Faire Linux inc.
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

"""This Class is a plugin for the Shinken Broker. It is in charge
to brok information of the service/host perfdatas into the influxdb
backend. http://influxdb.com/
"""

from shinken.basemodule import BaseModule
from shinken.log import logger
from shinken.misc.perfdata import PerfDatas
from influxdb import InfluxDBClient


properties = {
    'daemons': ['broker'],
    'type': 'influxdb_perfdata',
    'external': False,
}


# Called by the plugin manager to get a broker
def get_instance(mod_conf):
    logger.info("[influxdb broker] Get an influxdb data module for plugin %s" % mod_conf.get_name())
    instance = InfluxdbBroker(mod_conf)
    return instance


# Class for the influxdb Broker
# Get broks and send them to influxdb
class InfluxdbBroker(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.host = getattr(modconf, 'host', 'localhost')
        self.port = int(getattr(modconf, 'port', '8086'))
        self.user = getattr(modconf, 'user', 'root')
        self.password = getattr(modconf, 'password', 'root')
        self.database = getattr(modconf, 'database', 'database')
        self.use_udp = getattr(modconf, 'use_udp', '0') == '1'
        self.udp_port = int(getattr(modconf, 'udp_port', '4444'))

        self.buffer = []
        self.ticks = 0
        self.tick_limit = int(getattr(modconf, 'tick_limit', '300'))

    # Called by Broker so we can do init stuff
    # Conf from arbiter!
    def init(self):
        logger.info("[influxdb broker] I init the %s server connection to %s:%d" %
                    (self.get_name(), str(self.host), self.port))

        self.db = InfluxDBClient(self.host, self.port, self.user, self.password, self.database,
                                 self.use_udp, self.udp_port)

    # A service check result brok has just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data

        perf_data = data['perf_data']
        metrics = PerfDatas(perf_data).metrics

        # If no values, we can exit now
        if len(metrics) == 0:
            return

        hname = self.illegal_char.sub('_', data['host_name'])
        desc = self.illegal_char.sub('_', data['service_description'])
        check_time = int(data['last_chk'])

        try:
            logger.debug("[influxdb broker] Hostname: %s, Desc: %s, check time: %d, perfdata: %s"
                         % (hname, desc, check_time, str(perf_data)))
        except UnicodeEncodeError:
            pass

        post_data = []
        for e in metrics.values():
            post_data .append(
                {"points": [[check_time, e.value, e.uom, e.warning, e.critical, e.min, e.max]],
                 "name": "%s.%s.%s" % (hname, desc, e.name),
                 "columns": ["time", "value", "unit", "warning", "critical", "min", "max"]
                 }
            )

        try:
            logger.debug("[influxdb broker] Launching: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.buffer += post_data

    # A host check result brok has just arrived, we UPDATE data info with this
    def manage_host_check_result_brok(self, b):
        data = b.data

        perf_data = data['perf_data']
        metrics = PerfDatas(perf_data).metrics

        # If no values, we can exit now
        if len(metrics) == 0:
            return

        hname = self.illegal_char.sub('_', data['host_name'])
        check_time = int(data['last_chk'])

        try:
            logger.debug("[influxdb broker] Hostname %s, check time: %d, perfdata: %s"
                         % (hname, check_time, str(perf_data)))
        except UnicodeEncodeError:
            pass

        post_data = []
        for e in metrics.values():
            post_data .append(
                {"points": [[check_time, e.value, e.uom, e.warning, e.critical, e.min, e.max]],
                 "name": "%s.%s" % (hname, e.name),
                 "columns": ["time", "value", "unit", "warning", "critical", "min", "max"]
                 }
            )

        try:
            logger.debug("[influxdb broker] Launching: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.buffer += post_data

    def hook_tick(self, brok):

        if self.ticks >= self.tick_limit:
            logger.error("[influxdb broker] Buffering ticks exceeded. Freeing buffer")
            self.buffer = []
            self.ticks = 0

        if len(self.buffer) > 0:
            try:
                logger.error(str(self.buffer))
                self.db.write_points(self.buffer)
                self.buffer = []
                self.ticks = 0
            except:
                self.ticks += 1
                logger.error("[influxdb broker] Sending data Failed. Buffering state : %s / %s"
                             % (self.ticks, self.tick_limit))
