
from module.module import InfluxdbBroker

from module import get_instance

from shinken.objects.module import Module
from shinken.brok import Brok

import unittest2 as unittest


basic_dict_modconf = dict(
    module_name='influxdbBroker',
    module_type='influxdbBroker'
)


class TestInfluxdbBroker(unittest.TestCase):

    def setUp(self):
        self.basic_modconf = Module(basic_dict_modconf)

    def test_get_instance(self):
        result = get_instance(self.basic_modconf)
        self.assertIsInstance(result, InfluxdbBroker)

    def test_get_unknown_check_result_perfdata_points(self):
        tags = {"host_name": "testhello"}
        data = {
            'perf_data': 'ramused=1009MB;;;0;1982 swapused=540PT;;;0;3827 \
                memused=1550GB;2973;3964;0;5810',
            'time_stamp': 1403618279,
        }

        expected = [
            {'fields':
                {'max': 1982.0,
                 'unit': 'MB',
                 'value': 1009.0,
                 'min': 0.0},
                'time': 1403618279,
                'tags': {'host_name': 'testhello'},
                'measurement': 'metric_ramused'},
            {'fields':
                {'min': 0.0,
                 'max': 5810.0,
                 'value': 1550.0,
                 'warning': 2973.0,
                 'critical': 3964.0,
                 'unit': 'GB'},
                'time': 1403618279,
                'tags': {'host_name': 'testhello'},
                'measurement': 'metric_memused'},
            {'fields':
                {'max': 3827.0,
                 'unit': 'PT',
                 'value': 540.0,
                 'min': 0.0},
                'time': 1403618279,
                'tags': {'host_name': 'testhello'},
                'measurement': 'metric_swapused'}
        ]

        result = InfluxdbBroker.get_check_result_perfdata_points(
            get_instance(self.basic_modconf),
            data['perf_data'],
            data['time_stamp'],
            tags
        )
        print result
        self.assertEqual(expected, result)

    def test_get_check_result_perfdata_points(self):
        tags = {"host_name": "testname"}
        data = {
            'perf_data': 'ramused=1009MB;;;0;1982 swapused=540PT;;;0;3827 \
                memused=1550GB;2973;3964;0;5810'
        }
        timestamp = 1403618279

        expected = [
            {'fields':
                {'max': 1982.0,
                 'unit': 'MB',
                 'value': 1009.0,
                 'min': 0.0},
                'time': 1403618279,
                'tags': {'host_name': 'testname'},
                'measurement': 'metric_ramused'},
            {'fields':
                {'min': 0.0,
                 'max': 5810.0,
                 'value': 1550.0,
                 'warning': 2973.0,
                 'critical': 3964.0,
                 'unit': 'GB'},
                'time': 1403618279,
                'tags': {'host_name': 'testname'},
                'measurement': 'metric_memused'},
            {'fields':
                {'max': 3827.0,
                 'unit': 'PT',
                 'value': 540.0,
                 'min': 0.0},
                'time': 1403618279,
                'tags': {'host_name': 'testname'},
                'measurement': 'metric_swapused'}]

        result = InfluxdbBroker.get_check_result_perfdata_points(
            get_instance(self.basic_modconf),
            data['perf_data'],
            timestamp,
            tags
        )

        # print result

        self.assertEqual(expected, result)

    def test_get_state_update_points(self):
        tags = {'host_name': 'testname'}

        #the state type changes
        data = {
            'last_chk': 1403618279,
            'state': 'WARNING',
            'last_state': 'WARNING',
            'state_type': 'HARD',
            'last_state_type': 'SOFT',
            'output': 'BOB IS NOT HAPPY',
        }
        result = InfluxdbBroker.get_state_update_points(data, tags)
        expected = [
            {'fields':
                {'state_type': 'HARD',
                 'output': 'BOB IS NOT HAPPY',
                 'state': 'WARNING',
                 'event_type': 'ALERT'},
                'tags': {'host_name': 'testname'},
                'time': 1403618279,
                'measurement': 'EVENT'}]
        self.assertEqual(expected, result)

        #The state changes
        data = {
            'last_chk': 1403618279,
            'state': 'WARNING',
            'last_state': 'CRITICAL',
            'state_type': 'SOFT',
            'last_state_type': 'SOFT',
            'output': 'BOB IS NOT HAPPY',
        }
        result = InfluxdbBroker.get_state_update_points(data, tags)
        print result
        expected = [
            {'fields':
                {'state_type': 'SOFT',
                 'output': 'BOB IS NOT HAPPY',
                 'state': 'WARNING',
                 'event_type': 'ALERT'},
                'tags': {'host_name': 'testname'},
                'time': 1403618279, 'measurement': 'EVENT'}]
        self.assertEqual(expected, result)

        #Nothing changes
        data = {
            'last_chk': 1403618279,
            'state': 'WARNING',
            'last_state': 'WARNING',
            'state_type': 'SOFT',
            'last_state_type': 'SOFT',
            'output': 'BOB IS NOT HAPPY',
        }
        result = InfluxdbBroker.get_state_update_points(data, tags)
        expected = []
        self.assertEqual(expected, result)

    def test_init_defaults(self):
        broker = InfluxdbBroker(self.basic_modconf)

        self.assertEqual(broker.host, 'localhost')
        self.assertEqual(broker.port, 8086)
        self.assertEqual(broker.user, 'root')
        self.assertEqual(broker.password, 'root')
        self.assertEqual(broker.database, 'database')
        self.assertEqual(broker.use_udp, False)
        self.assertEqual(broker.udp_port, 4444)
        self.assertEqual(broker.tick_limit, 300)

    def test_init(self):
        modconf = Module(
            {
                'module_name': 'influxdbBroker',
                'module_type': 'influxdbBroker',
                'host': 'testhost',
                'port': '1111',
                'user': 'testuser',
                'password': 'testpassword',
                'database': 'testdatabase',
                'use_udp': '1',
                'udp_port': '2222',
                'tick_limit': '3333',
            }
        )

        broker = InfluxdbBroker(modconf)

        self.assertEqual(broker.host, 'testhost')
        self.assertEqual(broker.port, 1111)
        self.assertEqual(broker.user, 'testuser')
        self.assertEqual(broker.password, 'testpassword')
        self.assertEqual(broker.database, 'testdatabase')
        self.assertEqual(broker.use_udp, True)
        self.assertEqual(broker.udp_port, 2222)
        self.assertEqual(broker.tick_limit, 3333)

    def test_hook_tick(self):
        setattr(self.basic_modconf, 'use_udp', '1')

        data = [
            {
                "points": [["1", 1, 1.0], ["2", 2, 2.0]],
                "name": "foo",
                "columns": ["column_one", "column_two", "column_three"]
            }
        ]

        broker = InfluxdbBroker(self.basic_modconf)
        broker.init()
        broker.buffer.append(data)
        broker.ticks = 300
        broker.hook_tick(None)

        # We are not testing python-influxdb.
        # We are only making sure that the format of points we are sending
        # does not raise errors and that the buffer empties.
        self.assertEqual(broker.buffer, [])
        self.assertEqual(broker.ticks, 0)

    def test_hook_tick_limit(self):
        broker = InfluxdbBroker(self.basic_modconf)
        broker.tick_limit = 300
        broker.ticks = 299
        broker.buffer.append('this_wont_work_lol')
        broker.hook_tick(None)
        broker.hook_tick(None)
        self.assertEqual(broker.ticks, 0)
        self.assertEqual(broker.buffer, [])


class TestInfluxdbBrokerInstance(unittest.TestCase):

    def setUp(self):
        self.basic_modconf = Module(basic_dict_modconf)
        self.influx_broker = InfluxdbBroker(self.basic_modconf)

    def test_manage_log_brok(self):
        data = {
            'log': '[1402515279] HOST NOTIFICATION: admin;localhost;CRITICAL;notify-service-by-email;Connection refused'  # nopep8
        }
        brok = Brok('log', data)
        brok.prepare()

        broker = self.influx_broker
        broker.manage_log_brok(brok)

        # make sure that this has generated only 1 point
        self.assertEqual(len(broker.buffer), 1)
        point = broker.buffer[0]

        # validate the point
        expected = {'fields':
                    {'time': 1402515279,
                     'state': 'CRITICAL',
                     'contact': 'admin',
                     'notification_type': 'HOST',
                     'notification_method': 'notify-service-by-email',
                     'output': 'Connection refused'},
                    'time': 1402515279,
                    'tags': {'service_description': '_self_',
                             'host_name': 'localhost',
                             'event_type': 'NOTIFICATION'},
                    'measurement': 'EVENT'}
        self.assertEqual(expected, point)

        # A service notification's tags should include service_desc
        data['log'] = '[1402515279] SERVICE NOTIFICATION: admin;localhost;check-ssh;CRITICAL;notify-service-by-email;Connection refused'  # nopep8
        brok = Brok('log', data)
        brok.prepare()
        broker.buffer = []
        broker.manage_log_brok(brok)
        point = broker.buffer[0]
        self.assertEqual(point['measurement'], 'EVENT')
        self.assertEqual(point['tags']['service_description'], 'check-ssh')

    def test_log_brok_illegal_char(self):
        data = {
            'log': '[1329144231] SERVICE ALERT: www.cibc.com;www.cibc.com;WARNING;HARD;4;WARNING - load average: 5.04, 4.67, 5.04'  # nopep8
        }
        brok = Brok('log', data)
        brok.prepare()
        broker = self.influx_broker
        broker.manage_log_brok(brok)
        point = broker.buffer[0]
        self.assertEqual(point['measurement'], 'EVENT')
        self.assertEqual(point['tags']['host_name'], 'www.cibc.com')
        self.assertEqual(point['tags']['service_description'], 'www.cibc.com')

    def test_manage_unknown_host_check_result_brok(self):
        # Prepare the Brok
        data = {
            'time_stamp': 1234567890, 'return_code': '2',
            'host_name': 'test_host_0', 'output': 'Bob is not happy',
            'perf_data': 'rtt=9999'
        }
        brok = Brok('unknown_host_check_result', data)
        brok.prepare()

        # Send the brok
        broker = self.influx_broker
        broker.manage_unknown_host_check_result_brok(brok)

        self.assertEqual(
            broker.buffer[0],
            {'fields':
                {'unit': '', 'value': 9999.0},
                'time': 1234567890,
                'tags': {'host_name': 'test_host_0'},
                'measurement': 'metric_rtt'}
        )

    def test_manage_unknown_service_check_result_brok(self):
        # Prepare the Brok
        data = {
            'host_name': 'test_host_0', 'time_stamp': 1234567890,
            'service_description': 'test_ok_0', 'return_code': '1',
            'output': 'Bobby is not happy',
            'perf_data': 'rtt=9999;5;10;0;10000'
        }
        brok = Brok('unknown_service_check_result', data)
        brok.prepare()

        # Send the brok
        broker = self.influx_broker
        broker.manage_unknown_service_check_result_brok(brok)
        self.assertEqual(
            broker.buffer[0],
            {'fields':
                {'min': 0.0,
                 'max': 10000.0,
                 'value': 9999.0,
                 'warning': 5.0,
                 'critical': 10.0,
                 'unit': ''},
                'time': 1234567890,
                'tags': {'service_description': 'test_ok_0',
                         'host_name': 'test_host_0'},
                'measurement': 'metric_rtt'}
        )
