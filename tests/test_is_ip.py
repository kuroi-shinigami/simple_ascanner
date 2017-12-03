from unittest import TestCase

from simple_ascanner import is_ip


class TestIsIp(TestCase):
    def test_valid_string(self):
        self.assertTrue(is_ip('192.168.1.1'))

    def test_invalid_args(self):
        self.assertFalse(is_ip(1488255255255))
        self.assertFalse(is_ip({'1': '12.44'}))

    def test_invalid_inputs(self):
        self.assertFalse(is_ip('-192.168.1.1'))
        self.assertFalse(is_ip('256.256.256.256'))
        self.assertFalse(is_ip('-192.256.256.256'))
