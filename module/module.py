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

"""
This Class is a plugin for the Shinken Broker. It is in charge
to brok information of the services/hosts and events into the influxdb
backend. http://influxdb.com/
"""

from shinken.basemodule import BaseModule
from shinken.log import logger
from shinken.misc.perfdata import PerfDatas
from shinken.misc.logevent import LogEvent
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
                                 use_udp=self.use_udp, udp_port=self.udp_port, timeout=None)

    # Returns perfdata points
    @staticmethod
    def get_check_result_perfdata_points(perf_data, timestamp, name):

        points = []
        metrics = PerfDatas(perf_data).metrics

        for e in metrics.values():
            points.append(
                {"points": [[timestamp, e.value, e.uom, e.warning, e.critical, e.min, e.max]],
                 "name": "%s.%s" % (name, e.name),
                 "columns": ["time", "value", "unit", "warning", "critical", "min", "max"]
                 }
            )

        return points

    # Returns state_update points for a given check_result_brok data
    @staticmethod
    def get_state_update_points(data, name):
        points = []

        if data['state'] != data['last_state'] or \
                data['state_type'] != data['last_state_type']:

            points.append(
                {
                    "points": [[
                        data['last_chk'],
                        data['state'],
                        data['state_type'],
                        #We should not bother posting attempt
                        #if max_check_attempts is not available
                        #data['attempt'],
                        #data['max_check_attempts']
                        data['output']
                    ]],
                    "name": "%s._events_.ALERT" % name,
                    "columns": [
                        "time",
                        "state",
                        "state_type",
                        #"current_check_attempt",
                        #"max_check_attempts",
                        "output"
                    ]
                }
            )

        return points

    # A service check result brok has just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data
        name = "%s.%s" % (
            self.illegal_char.sub('_', data['host_name']),
            self.illegal_char.sub('_', data['service_description'])
        )

        post_data = []

        post_data.extend(
            self.get_check_result_perfdata_points(
                b.data['perf_data'],
                b.data['last_chk'],
                name
            )
        )

        post_data.extend(
            self.get_state_update_points(b.data, name)
        )

        try:
            logger.debug("[influxdb broker] Launching: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.buffer.extend(post_data)

    # A host check result brok has just arrived, we UPDATE data info with this
    def manage_host_check_result_brok(self, b):
        data = b.data
        name = self.illegal_char.sub('_', data['host_name']) + "._self_"

        post_data = []

        post_data.extend(
            self.get_check_result_perfdata_points(
                b.data['perf_data'],
                b.data['last_chk'],
                name
            )
        )

        post_data.extend(
            self.get_state_update_points(b.data, name)
        )

        try:
            logger.debug("[influxdb broker] Launching: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.buffer.extend(post_data)

    def manage_unknown_host_check_result_brok(self, b):
        data = b.data
        name = self.illegal_char.sub('_', data['host_name'])

        post_data = []

        post_data.extend(
            self.get_check_result_perfdata_points(
                b.data['perf_data'],
                b.data['time_stamp'],
                name
            )
        )

        try:
            logger.debug("[influxdb broker] Launching: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.buffer.extend(post_data)

    def manage_unknown_service_check_result_brok(self, b):
        data = b.data
        name = "%s.%s" % (
            self.illegal_char.sub('_', data['host_name']),
            self.illegal_char.sub('_', data['service_description'])
        )

        post_data = []

        post_data.extend(
            self.get_check_result_perfdata_points(
                b.data['perf_data'],
                b.data['time_stamp'],
                name
            )
        )

        try:
            logger.debug("[influxdb broker] Launching: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.buffer.extend(post_data)

    # A log brok has arrived, we UPDATE data info with this
    def manage_log_brok(self, b):
        log = b.data['log']
        event = LogEvent(log)

        if len(event) > 0:
            # include service_desc in the table name if present
            if 'service_desc' in event and event['service_desc'] is not None:
                name = "%s.%s._events_.%s" % (
                    self.illegal_char.sub('_', event['hostname']),
                    self.illegal_char.sub('_', event['service_desc']),
                    event['event_type']
                )
            else:
                name = "%s._events_.%s" % (
                    self.illegal_char.sub('_', event['hostname']),
                    event['event_type']
                )

            point = {
                "points": [[]],
                "name": name,
                "columns": []
            }

            # Add each property of the service in the point
            for prop in [prop for prop in event if prop[0] not in ['hostname', 'event_type', 'service_desc']]:
                point['columns'].append(prop[0])
                point['points'][0].append(prop[1])

            self.buffer.append(point)

    def hook_tick(self, brok):

        if self.ticks >= self.tick_limit:
            logger.error("[influxdb broker] Buffering ticks exceeded. Freeing buffer")
            self.buffer = []
            self.ticks = 0

        if len(self.buffer) > 0:
            try:
                self.db.write_points(self.buffer)
                self.buffer = []
                self.ticks = 0
            except:
                self.ticks += 1
                logger.error("[influxdb broker] Sending data Failed. Buffering state : %s / %s"
                             % (self.ticks, self.tick_limit))
