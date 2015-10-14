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

import json
import threading

from shinken.basemodule import BaseModule
from shinken.log import logger
from shinken.misc.perfdata import PerfDatas
from influxdb import InfluxDBClient

# LogEvent is only available in shinken>2.0.3
try:
    from shinken.misc.logevent import LogEvent
except ImportError:
    from logevent import LogEvent


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
        self.use_https = getattr(modconf, 'use_https', False)
        self.use_udp = getattr(modconf, 'use_udp', '0') == '1'
        self.udp_port = int(getattr(modconf, 'udp_port', '4444'))

        self._lock = threading.Lock()
        self.buffer = []
        self.ticks = 0
        self.tick_limit = int(getattr(modconf, 'tick_limit', '300'))

    def extend_buffer(self, other):
        with self._lock:
            self.buffer.extend(other)

    # Called by Broker so we can do init stuff
    # Conf from arbiter!
    def init(self):
        logger.info(
            "[influxdb broker] I init the %s server connection to %s:%d" %
            (self.get_name(), str(self.host), self.port)
        )

        self.db = InfluxDBClient(
            self.host, self.port, self.user, self.password, self.database,
            ssl=self.use_https,use_udp=self.use_udp,
            udp_port=self.udp_port, timeout=None
        )

    def get_check_result_perfdata_points(self, perf_data, timestamp, tags={}):
        """
        :param perf_data: Perf data of the brok
        :param timestamp: Timestamp of the check result
        :param tags: Tags for the point
        :return: List of perfdata points
        """
        points = []
        metrics = PerfDatas(perf_data).metrics

        for e in metrics.values():
            fields = {}
            fields_mappings = [
                ('value', 'value'),
                ('uom', 'unit'),
                ('warning', 'warning'),
                ('critical', 'critical'),
                ('min', 'min'),
                ('max', 'max')
            ]
            for mapping in fields_mappings:
                value = getattr(e, mapping[0], None)
                if value is not None:
                    if isinstance(value, (int, long)):
                        value = float(value)
                    fields[mapping[1]] = value

            if fields:
                point = {
                    "measurement": 'metric_%s' % self.illegal_char.sub('_', e.name),
                    "time": timestamp,
                    "fields": fields,
                    "tags": tags,
                }
                points.append(point)

        return points

    @staticmethod
    def get_state_update_points(data, tags={}):
        """
        :param tags: Tags for the points
        :return: Returns ALERT points for a given check_result_brok data
        """
        points = []

        if data['state'] != data['last_state'] or \
                data['state_type'] != data['last_state_type']:

            points.append(
                {
                    "measurement": "EVENT",
                    "tags": tags,
                    "time": data['last_chk'],
                    "fields": {
                        "event_type": 'ALERT',
                        "state": data['state'],
                        "state_type": data['state_type'],
                        "output": data['output'],
                    },
                }
            )

        return points

    @staticmethod
    def get_state_points(data, name, tags={}):
        """
        :param tags: Tags for the points
        :param name: HOST_STATE or SERVICE_STATE
        :return: Returns 'name' points for a given check_result_brok data
        """
        points = []

        points.append(
            {
                "measurement": name,
                "tags": tags,
                "time": data['last_chk'],
                "fields": {
                    "state_type": data['state_type'],
                    'acknowledged': int(data['problem_has_been_acknowledged']),
                    "output": data['output'],
                    "state": data['state_id'],
                    "last_check": data['last_chk'],
                    "last_state_change": data['last_state_change']
                },
            }
        )

        return points

    # A service check result brok has just arrived,
    # we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data

        tags = {
            "host_name": data['host_name'],
            "service_description": data['service_description']
        }

        post_data = []

        post_data.extend(
            self.get_check_result_perfdata_points(
                b.data['perf_data'],
                b.data['last_chk'],
                tags=tags
            )
        )

        post_data.extend(
            self.get_state_update_points(b.data, tags)
        )

        post_data.extend(
            self.get_state_points(b.data, "SERVICE_STATE", tags)
        )

        try:
            logger.debug("[influxdb broker] Generated points: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.extend_buffer(post_data)

    # A host check result brok has just arrived, we UPDATE data info with this
    def manage_host_check_result_brok(self, b):
        data = b.data
        host_name = data['host_name']

        tags = {
            "host_name": host_name,
            "service_description": '__host__',
        }

        post_data = []

        post_data.extend(
            self.get_check_result_perfdata_points(
                b.data['perf_data'],
                b.data['last_chk'],
                tags=tags
            )
        )

        post_data.extend(
            self.get_state_update_points(
                b.data,
                tags
            )
        )

        post_data.extend(
            self.get_state_points(b.data, "HOST_STATE", tags)
        )

        try:
            logger.debug("[influxdb broker] Generated points: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.extend_buffer(post_data)

    def manage_unknown_host_check_result_brok(self, b):
        data = b.data

        tags = {
            "host_name": data['host_name']
        }

        post_data = []

        post_data.extend(
            self.get_check_result_perfdata_points(
                b.data['perf_data'],
                b.data['time_stamp'],
                tags=tags
            )
        )

        try:
            logger.debug("[influxdb broker] Generated points: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.extend_buffer(post_data)

    def manage_unknown_service_check_result_brok(self, b):
        data = b.data

        tags = {
            "host_name": data['host_name'],
            "service_description": data['service_description']
        }

        post_data = []

        post_data.extend(
            self.get_check_result_perfdata_points(
                b.data['perf_data'],
                b.data['time_stamp'],
                tags=tags
            )
        )

        try:
            logger.debug("[influxdb broker] Generated points: %s" % str(post_data))
        except UnicodeEncodeError:
            pass

        self.extend_buffer(post_data)

    # A log brok has arrived, we UPDATE data info with this
    def manage_log_brok(self, b):
        log = b.data['log']
        event = LogEvent(log)

        if len(event) > 0:
            # include service_description in the table name if present
            if 'service_desc' in event and event['service_desc'] is not None:
                service_description = event['service_desc']
            else:
                service_description = '_self_'

            point = {
                "measurement": "EVENT",
                "time": event['time'],
                "fields": {},
                "tags": {
                    "host_name": event['hostname'],
                    "service_description": service_description,
                    "event_type": event['event_type'],
                }
            }

            # Add each property of the service in the point
            for prop in [
                prop for prop in event
                if prop[0] not in ['hostname', 'event_type', 'service_desc']
            ]:
                point['fields'][prop[0]] = prop[1]

            try:
                logger.debug("[influxdb broker] Generated points: %s" % str([point]))
            except UnicodeEncodeError:
                pass

            self.extend_buffer([point])

    def hook_tick(self, brok):

        if self.ticks >= self.tick_limit:
            with self._lock:
                buffer = self.buffer
                self.buffer = []
            logger.error(
                "[influxdb broker] Buffering ticks exceeded. "
                "Freeing buffer, lost %d entries" % len(buffer)
            )
            self.ticks = 0

        if len(self.buffer) > 0:
            with self._lock:
                buffer = self.buffer
                self.buffer = []
            try:
                try:
                    logger.debug("[influxdb broker] Writing points: %s" % str(buffer))
                except UnicodeEncodeError:
                    pass
                self.db.write_points(buffer, time_precision='s')
            except Exception as e:
                self.ticks += 1
                logger.error("[influxdb broker] %s" % e)
                logger.error(
                    "[influxdb broker] Sending data Failed. "
                    "Buffering state : %s / %s"
                    % (self.ticks, self.tick_limit)
                )
                with self._lock:
                    buffer.extend(self.buffer)
                    self.buffer = buffer
            else:
                self.ticks = 0
