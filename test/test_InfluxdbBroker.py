from module.module import InfluxdbBroker
from shinken.objects.module import Module
from shinken.brok import Brok
import unittest


class TestInfluxdbBroker(unittest.TestCase):

    def setUp(self):
        self.basic_modconf = Module(
            {
                'module_name': 'influxdbBroker',
                'module_type': 'influxdbBroker',
            }
        )

    def test_get_unknown_check_result_perfdata_points(self):
        name = 'testname'
        data = {
            'perf_data': 'ramused=1009MB;;;0;1982 swapused=540PT;;;0;3827 memused=1550GB;2973;3964;0;5810',
            'time_stamp': 1403618279,
        }

        expected = [
            {'points': [[1403618279, 1009, 'MB', None, None, 0, 1982]],
             'name': 'testname.ramused',
             'columns': ['time', 'value', 'unit', 'warning', 'critical', 'min', 'max']},
            {'points': [[1403618279, 1550, 'GB', 2973, 3964, 0, 5810]],
             'name': 'testname.memused',
             'columns': ['time', 'value', 'unit', 'warning', 'critical', 'min', 'max']},
            {'points': [[1403618279, 540, 'PT', None, None, 0, 3827]],
             'name': 'testname.swapused',
             'columns': ['time', 'value', 'unit', 'warning', 'critical', 'min', 'max']}
        ]

        result = InfluxdbBroker.get_check_result_perfdata_points(
            data['perf_data'],
            data['time_stamp'],
            name
        )
        self.assertEqual(expected, result)

    def test_get_check_result_perfdata_points(self):
        name = 'testname'
        data = {
            'perf_data': 'ramused=1009MB;;;0;1982 swapused=540PT;;;0;3827 memused=1550GB;2973;3964;0;5810',
            'last_chk': 1403618279,
        }

        expected = [
            {'points': [[1403618279, 1009, 'MB', None, None, 0, 1982]],
             'name': 'testname.ramused',
             'columns': ['time', 'value', 'unit', 'warning', 'critical', 'min', 'max']},
            {'points': [[1403618279, 1550, 'GB', 2973, 3964, 0, 5810]],
             'name': 'testname.memused',
             'columns': ['time', 'value', 'unit', 'warning', 'critical', 'min', 'max']},
            {'points': [[1403618279, 540, 'PT', None, None, 0, 3827]],
             'name': 'testname.swapused',
             'columns': ['time', 'value', 'unit', 'warning', 'critical', 'min', 'max']}
        ]
        result = InfluxdbBroker.get_check_result_perfdata_points(
            data['perf_data'],
            data['last_chk'],
            name
        )
        self.assertEqual(expected, result)

    def test_get_state_update_points(self):
        name = 'testname'

        #the state type changes
        data = {
            'last_chk': 1403618279,
            'state': 'WARNING',
            'last_state': 'WARNING',
            'state_type': 'HARD',
            'last_state_type': 'SOFT',
            'output': 'BOB IS NOT HAPPY',
        }
        result = InfluxdbBroker.get_state_update_points(data, name)
        expected = [
            {'points': [[1403618279, 'WARNING', 'HARD', 'BOB IS NOT HAPPY']],
             'name': 'testname._events_.alerts',
             'columns': ['time', 'state', 'state_type', 'output']}
        ]
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
        result = InfluxdbBroker.get_state_update_points(data, name)
        expected = [
            {'points': [[1403618279, 'WARNING', 'SOFT', 'BOB IS NOT HAPPY']],
             'name': 'testname._events_.alerts',
             'columns': ['time', 'state', 'state_type', 'output']}
        ]
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
        result = InfluxdbBroker.get_state_update_points(data, name)
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

    def test_manage_log_brok(self):
        data = {
            'log': '[1402515279] HOST NOTIFICATION: admin;localhost;CRITICAL;notify-service-by-email;Connection refused'
        }
        brok = Brok('log', data)
        brok.prepare()

        broker = InfluxdbBroker(self.basic_modconf)
        broker.manage_log_brok(brok)

        # We are not testing shinken.LogEvent
        # Only make sure that this has generated 1 point
        self.assertEqual(len(broker.buffer), 1)
        point = broker.buffer[0]

        # That the point's name is appropriate (host._events_.[event_type])
        self.assertEqual(point['name'], 'localhost._events_.NOTIFICATION')

        # And that there is as much columns as there is points
        # (manage_log_brok has a special way of creating points)
        self.assertEqual(
            len(point['points'][0]),
            len(point['columns'])
        )

        # A service notification's name should be different (host.service._events_.[event_type])
        data['log'] = '[1402515279] SERVICE NOTIFICATION: admin;localhost;check-ssh;CRITICAL;notify-service-by-email;Connection refused'
        brok = Brok('log', data)
        brok.prepare()
        broker.buffer = []
        broker.manage_log_brok(brok)
        point = broker.buffer[0]
        self.assertEqual(point['name'], 'localhost.check-ssh._events_.NOTIFICATION')


