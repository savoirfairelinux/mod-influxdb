from module.module import InfluxdbBroker
import unittest
from shinken.objects.module import Module


class TestInfluxdbBroker(unittest.TestCase):

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
        result = InfluxdbBroker.get_check_result_perfdata_points(data, name)
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

        #defaults
        modconf = Module(
            {
                'module_name': 'influxdbBroker',
                'module_type': 'influxdbBroker',
            }
        )

        broker = InfluxdbBroker(modconf)

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