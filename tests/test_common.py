from unittest import TestCase


from simple_ascanner import ip2int, int2ip, iprange


class TestFunctions(TestCase):
    def test_ip2str(self):
        """Checking if it works"""
        self.assertEqual(ip2int('127.0.0.1'), 2130706433)

    def test_str2ipr(self):
        """Checking if it works"""
        self.assertEqual('127.0.0.1', int2ip(2130706433))

    def test_iprange(self):
        self.assertEqual(len(list(iprange('127.0.0.1'))), 1)
        self.assertEqual(len(list(iprange('127.0.0.1', '127.0.0.2'))), 2)
