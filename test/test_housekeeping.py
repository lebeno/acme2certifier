#!/usr/bin/python
# -*- coding: utf-8 -*-
""" unittests for account.py """
# pylint: disable=C0302, C0415, R0904, R0913, R0914, R0915, W0212
import unittest
import sys
from unittest.mock import patch, MagicMock, mock_open
import configparser

sys.path.insert(0, '.')
sys.path.insert(1, '..')

class FakeDBStore(object):
    """ face DBStore class needed for mocking """
    # pylint: disable=W0107, R0903
    pass

class TestACMEHandler(unittest.TestCase):
    """ test class for ACMEHandler """
    acme = None
    def setUp(self):
        """ setup unittest """
        models_mock = MagicMock()
        models_mock.acme.db_handler.DBstore.return_value = FakeDBStore
        modules = {'acme.db_handler': models_mock}
        patch.dict('sys.modules', modules).start()
        import logging
        logging.basicConfig(level=logging.CRITICAL)
        self.logger = logging.getLogger('test_a2c')
        from acme.challenge import Challenge
        from acme.housekeeping import Housekeeping
        self.challenge = Challenge(False, 'http://tester.local', self.logger)
        self.housekeeping = Housekeeping(False, self.logger)

    def test_001_housekeeping__certificatelist_get(self):
        """ test Housekeeping._certificatelist_get() """
        self.housekeeping.dbstore.certificatelist_get.return_value = 'foo'
        self.assertEqual('foo', self.housekeeping._certificatelist_get())

    def test_002_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - empty list"""
        cert_list = []
        self.assertEqual([], self.housekeeping._convert_data(cert_list))

    def test_003_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - orders__expire to convert """
        cert_list = [{'foo': 'bar', 'order.expires': 1577840461}]
        self.assertEqual([{'foo': 'bar', 'order.expires': '2020-01-01 01:01:01', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.expire_date': '', 'certificate.issue_date': ''}], self.housekeeping._convert_data(cert_list))

    def test_004_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - orders__expires and authentication__expires to convert (not in list) """
        cert_list = [{'foo': 'bar', 'order.expires': 1577840461, 'authentication.expires': 1577840462}]
        self.assertEqual([{'authentication.expires': 1577840462, 'foo': 'bar', 'order.expires': '2020-01-01 01:01:01', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.expire_date': '', 'certificate.issue_date': ''}], self.housekeeping._convert_data(cert_list))

    def test_005_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - orders__expires and authorization__expires to convert (not in list) """
        cert_list = [{'foo': 'bar', 'order.expires': 1577840461, 'authorization.expires': 1577840462}]
        self.assertEqual([{'authorization.expires': '2020-01-01 01:01:02', 'foo': 'bar', 'order.expires': '2020-01-01 01:01:01', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.expire_date': '', 'certificate.issue_date': ''}], self.housekeeping._convert_data(cert_list))

    def test_006_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - list containing bogus values"""
        cert_list = [{'foo': 'bar'}]
        self.assertEqual([{'foo': 'bar', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.expire_date': '', 'certificate.issue_date': ''}], self.housekeeping._convert_data(cert_list))

    def test_007_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - list contains only issue_uts """
        cert_list = [{'foo': 'bar', 'certificate.issue_uts': 0}]
        self.assertEqual([{'foo': 'bar', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.expire_date': '', 'certificate.issue_date': ''}], self.housekeeping._convert_data(cert_list))

    def test_008_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - list contains only expire_uts """
        cert_list = [{'foo': 'bar', 'certificate.expire_uts': 0}]
        self.assertEqual([{'foo': 'bar', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.expire_date': '', 'certificate.issue_date': ''}], self.housekeeping._convert_data(cert_list))

    def test_009_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - list contains both issue_uts and expire_uts """
        cert_list = [{'foo': 'bar', 'certificate.expire_uts': 1577840461, 'certificate.issue_uts': 1577840462}]
        self.assertEqual([{'foo': 'bar', 'certificate.expire_uts': 1577840461, 'certificate.expire_date': '2020-01-01 01:01:01', 'certificate.issue_date': '2020-01-01 01:01:02', 'certificate.issue_uts': 1577840462}], self.housekeeping._convert_data(cert_list))

    def test_010_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - list contains both uts with 0 """
        cert_list = [{'foo': 'bar', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0}]
        self.assertEqual([{'foo': 'bar', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.expire_date': '', 'certificate.issue_date': ''}], self.housekeeping._convert_data(cert_list))

    def test_011_housekeeping__convert_data(self):
        """ test Housekeeping._convert_data() - list contains both uts with 0 and a bogus cert_raw """
        cert_list = [{'foo': 'bar', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.cert_raw': 'cert_raw'}]
        self.assertEqual([{'foo': 'bar', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.expire_date': '', 'certificate.issue_date': '', 'certificate.cert_raw': 'cert_raw', 'certificate.serial': ''}], self.housekeeping._convert_data(cert_list))

    @patch('acme.housekeeping.cert_serial_get')
    @patch('acme.housekeeping.cert_dates_get')
    def test_012_housekeeping__convert_data(self, mock_dates, mock_serial):
        """ test Housekeeping._convert_data() - list contains both uts with 0 and a bogus cert_raw """
        cert_list = [{'foo': 'bar', 'certificate.expire_uts': 0, 'certificate.issue_uts': 0, 'certificate.cert_raw': 'cert_raw'}]
        mock_dates.return_value = (1577840461, 1577840462)
        mock_serial.return_value = 'serial'
        self.assertEqual([{'foo': 'bar', 'certificate.expire_uts': 1577840462, 'certificate.issue_uts': 1577840461, 'certificate.serial': 'serial', 'certificate.expire_date': '2020-01-01 01:01:02', 'certificate.issue_date': '2020-01-01 01:01:01', 'certificate.cert_raw': 'cert_raw'}], self.housekeeping._convert_data(cert_list))

    def test_013_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - both lists are empty """
        field_list = []
        cert_list = []
        self.assertEqual([], self.housekeeping._to_list(field_list, cert_list))

    def test_014_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - cert_list is empty """
        field_list = ['foo', 'bar']
        cert_list = []
        self.assertEqual([['foo', 'bar']], self.housekeeping._to_list(field_list, cert_list))

    def test_015_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - one cert in list """
        field_list = ['foo', 'bar']
        cert_list = [{'foo': 'foo1', 'bar': 'bar1'}]
        self.assertEqual([['foo', 'bar'], ['foo1', 'bar1']], self.housekeeping._to_list(field_list, cert_list))

    def test_016_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - one incomplete cert in list """
        field_list = ['foo', 'bar']
        cert_list = [{'foo': 'foo1'}]
        self.assertEqual([['foo', 'bar'], ['foo1', '']], self.housekeeping._to_list(field_list, cert_list))

    def test_017_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - two certs in list """
        field_list = ['foo', 'bar']
        cert_list = [{'foo': 'foo1', 'bar': 'bar1'}, {'foo': 'foo2', 'bar': 'bar2'}]
        self.assertEqual([['foo', 'bar'], ['foo1', 'bar1'], ['foo2', 'bar2']], self.housekeeping._to_list(field_list, cert_list))

    def test_018_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - two certs in list but on bogus """
        field_list = ['foo', 'bar']
        cert_list = [{'foo': 'foo1', 'bar': 'bar1'}, {'foo': 'foo2'}]
        self.assertEqual([['foo', 'bar'], ['foo1', 'bar1'], ['foo2', '']], self.housekeeping._to_list(field_list, cert_list))

    def test_019_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - one line contains LF """
        field_list = ['foo', 'bar']
        cert_list = [{'foo': 'fo\no1', 'bar': 'bar1'}, {'foo': 'foo2'}]
        self.assertEqual([['foo', 'bar'], ['foo1', 'bar1'], ['foo2', '']], self.housekeeping._to_list(field_list, cert_list))

    def test_020_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - one line contains CRLF """
        field_list = ['foo', 'bar']
        cert_list = [{'foo': 'fo\r\no1', 'bar': 'bar1'}, {'foo': 'foo2'}]
        self.assertEqual([['foo', 'bar'], ['foo1', 'bar1'], ['foo2', '']], self.housekeeping._to_list(field_list, cert_list))

    def test_021_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - one line contains CR """
        field_list = ['foo', 'bar']
        cert_list = [{'foo': 'fo\ro1', 'bar': 'bar1'}, {'foo': 'foo2'}]
        self.assertEqual([['foo', 'bar'], ['foo1', 'bar1'], ['foo2', '']], self.housekeeping._to_list(field_list, cert_list))

    def test_022_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - integer in dictionary """
        field_list = ['foo', 'bar']
        cert_list = [{'foo': 'fo\ro1', 'bar': 100}]
        self.assertEqual([['foo', 'bar'], ['foo1', 100]], self.housekeeping._to_list(field_list, cert_list))

    def test_023_housekeeping__to_list(self):
        """ test Housekeeping._to_list() - float in dictionary """
        field_list = ['foo', 'bar']
        cert_list = [{'foo': 'fo\ro1', 'bar': 10.23}]
        self.assertEqual([['foo', 'bar'], ['foo1', 10.23]], self.housekeeping._to_list(field_list, cert_list))

    def test_024_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - empty list """
        account_list = []
        self.assertEqual([], self.housekeeping._to_acc_json(account_list))

    def test_025_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - bogus list """
        account_list = [{'foo': 'bar'}]
        self.assertEqual([{'error_list': [{'foo': 'bar'}]}], self.housekeeping._to_acc_json(account_list))

    def test_026_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - bogus list """
        account_list = [{'account.name': 'account.name'}]
        self.assertEqual([{'error_list': [{'account.name': 'account.name'}]}], self.housekeeping._to_acc_json(account_list))

    def test_027_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - bogus list """
        account_list = [{'account.name': 'account.name01', 'order.name': 'order.name01'}]
        self.assertEqual([{'error_list': [{'account.name': 'account.name01', 'order.name': 'order.name01'}]}], self.housekeeping._to_acc_json(account_list))

    def test_028_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - bogus list """
        account_list = [{'account.name': 'account.name01', 'order.name': 'order.name01', 'authorization.name': 'authorization.name01'}]
        self.assertEqual([{'error_list': [{'account.name': 'account.name01', 'authorization.name': 'authorization.name01', 'order.name': 'order.name01'}]}], self.housekeeping._to_acc_json(account_list))

    def test_029_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - complete list """
        account_list = [
            {'account.name': 'account.name01', 'order.name': 'order.name01', 'authorization.name': 'authorization.name01', 'challenge.name': 'challenge.name01'}
            ]
        result_list = [{'account.name': 'account.name01', 'orders': [{'order.name': 'order.name01', 'authorizations': [{'authorization.name': 'authorization.name01', 'challenges': [{'challenge.name': 'challenge.name01'}]}]}]}]
        self.assertEqual(result_list, self.housekeeping._to_acc_json(account_list))

    def test_030_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - two challenges """
        account_list = [
            {'account.name': 'account.name01', 'order.name': 'order.name01', 'authorization.name': 'authorization.name01', 'challenge.name': 'challenge.name01'},
            {'account.name': 'account.name01', 'order.name': 'order.name01', 'authorization.name': 'authorization.name01', 'challenge.name': 'challenge.name02'}
            ]
        result_list = [{'account.name': 'account.name01', 'orders': [{'order.name': 'order.name01', 'authorizations': [{'authorization.name': 'authorization.name01', 'challenges': [{'challenge.name': 'challenge.name01'}, {'challenge.name': 'challenge.name02'}]}]}]}]
        self.assertEqual(result_list, self.housekeeping._to_acc_json(account_list))

    def test_031_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - two authorizations """
        account_list = [
            {'account.name': 'account.name01', 'order.name': 'order.name01', 'authorization.name': 'authorization.name01', 'challenge.name': 'challenge.name01'},
            {'account.name': 'account.name01', 'order.name': 'order.name01', 'authorization.name': 'authorization.name02', 'challenge.name': 'challenge.name02'}
            ]
        result_list = [{'account.name': 'account.name01', 'orders': [{'order.name': 'order.name01', 'authorizations': [{'authorization.name': 'authorization.name01', 'challenges': [{'challenge.name': 'challenge.name01'}]}, {'authorization.name': 'authorization.name02', 'challenges': [{'challenge.name': 'challenge.name02'}]}]}]}]
        self.assertEqual(result_list, self.housekeeping._to_acc_json(account_list))

    def test_032_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - two orders """
        account_list = [
            {'account.name': 'account.name01', 'order.name': 'order.name01', 'authorization.name': 'authorization.name01', 'challenge.name': 'challenge.name01'},
            {'account.name': 'account.name01', 'order.name': 'order.name02', 'authorization.name': 'authorization.name02', 'challenge.name': 'challenge.name02'}
            ]
        result_list = [{'account.name': 'account.name01', 'orders': [{'order.name': 'order.name01', 'authorizations': [{'authorization.name': 'authorization.name01', 'challenges': [{'challenge.name': 'challenge.name01'}]}]}, {'order.name': 'order.name02', 'authorizations': [{'authorization.name': 'authorization.name02', 'challenges': [{'challenge.name': 'challenge.name02'}]}]}]}]
        self.assertEqual(result_list, self.housekeeping._to_acc_json(account_list))

    def test_033_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - two accounts """
        account_list = [
            {'account.name': 'account.name01', 'order.name': 'order.name01', 'authorization.name': 'authorization.name01', 'challenge.name': 'challenge.name01'},
            {'account.name': 'account.name02', 'order.name': 'order.name02', 'authorization.name': 'authorization.name02', 'challenge.name': 'challenge.name02'}
            ]
        result_list = [{'account.name': 'account.name01', 'orders': [{'order.name': 'order.name01', 'authorizations': [{'authorization.name': 'authorization.name01', 'challenges': [{'challenge.name': 'challenge.name01'}]}]}]}, {'account.name': 'account.name02', 'orders': [{'order.name': 'order.name02', 'authorizations': [{'authorization.name': 'authorization.name02', 'challenges': [{'challenge.name': 'challenge.name02'}]}]}]}]
        self.assertEqual(result_list, self.housekeeping._to_acc_json(account_list))

    def test_034_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - complete list with subkeys"""
        account_list = [
            {'account.name': 'account.name01', 'account.foo': 'account.foo', 'order.name': 'order.name01', 'order.foo': 'order.foo', 'authorization.name': 'authorization.name01', 'authorization.foo': 'authorization.foo', 'challenge.name': 'challenge.name01', 'challenge.foo': 'challenge.foo'}
            ]
        result_list = [{'account.name': 'account.name01', 'account.foo': 'account.foo', 'orders': [{'order.name': 'order.name01', 'order.foo': 'order.foo', 'authorizations': [{'authorization.name': 'authorization.name01', 'authorization.foo': 'authorization.foo', 'challenges': [{'challenge.name': 'challenge.name01', 'challenge.foo': 'challenge.foo'}]}]}]}]
        self.assertEqual(result_list, self.housekeeping._to_acc_json(account_list))

    def test_035_housekeeping__to_acc_json(self):
        """ test Housekeeping._to_acc_list() - complete list """
        account_list = [
            {'account.name': 'account.name01', 'order.name': 'order.name01', 'authorization.name': 'authorization.name01', 'challenge.name': 'challenge.name01'},
            {'foo': 'bar'}]
        result_list = [{'account.name': 'account.name01', 'orders': [{'order.name': 'order.name01', 'authorizations': [{'authorization.name': 'authorization.name01', 'challenges': [{'challenge.name': 'challenge.name01'}]}]}]}, {'error_list': [{'foo': 'bar'}]}]
        self.assertEqual(result_list, self.housekeeping._to_acc_json(account_list))

    def test_036_housekeeping__fieldlist_normalize(self):
        """ test Certificate._fieldlist_normalize() - empty field_list """
        field_list = {}
        prefix = 'prefix'
        self.assertEqual({}, self.housekeeping._fieldlist_normalize(field_list, prefix))

    def test_037_housekeeping__fieldlist_normalize(self):
        """ test Certificate._fieldlist_normalize() - one ele """
        field_list = ['foo__bar']
        prefix = 'prefix'
        self.assertEqual({'foo__bar': 'foo.bar'}, self.housekeeping._fieldlist_normalize(field_list, prefix))

    def test_038_housekeeping__fieldlist_normalize(self):
        """ test Certificate._fieldlist_normalize() - two ele """
        field_list = ['foo__bar', 'bar__foo']
        prefix = 'prefix'
        self.assertEqual({'bar__foo': 'bar.foo', 'foo__bar': 'foo.bar'}, self.housekeeping._fieldlist_normalize(field_list, prefix))

    def test_039_housekeeping__fieldlist_normalize(self):
        """ test Certificate._fieldlist_normalize() - one ele without __ """
        field_list = ['foo']
        prefix = 'prefix'
        self.assertEqual({'foo': 'prefix.foo'}, self.housekeeping._fieldlist_normalize(field_list, prefix))

    def test_040_housekeeping__fieldlist_normalize(self):
        """ test Certificate._fieldlist_normalize() - two ele without __ """
        field_list = ['foo', 'bar']
        prefix = 'prefix'
        self.assertEqual({'foo': 'prefix.foo', 'bar': 'prefix.bar'}, self.housekeeping._fieldlist_normalize(field_list, prefix))

    def test_041_housekeeping__fieldlist_normalize(self):
        """ test Certificate._fieldlist_normalize() - status handling """
        field_list = ['foo__status__name']
        prefix = 'prefix'
        self.assertEqual({'foo__status__name': 'foo.status.name'}, self.housekeeping._fieldlist_normalize(field_list, prefix))

    def test_042_housekeeping__fieldlist_normalize(self):
        """ test Certificate._fieldlist_normalize() - status handling """
        field_list = ['foo__bar__name']
        prefix = 'prefix'
        self.assertEqual({'foo__bar__name': 'bar.name'}, self.housekeeping._fieldlist_normalize(field_list, prefix))

    def test_043_housekeeping__fieldlist_normalize(self):
        """ test Certificate._fieldlist_normalize() - status handling """
        field_list = ['status__name']
        prefix = 'prefix'
        self.assertEqual({'status__name': 'status.name'}, self.housekeeping._fieldlist_normalize(field_list, prefix))

    def test_044_housekeeping__lists_normalize(self):
        """ test Certificate._fieldlist_normalize() - one value """
        field_list = ['foo', 'foo__bar', 'bar__foo']
        value_list = [{'foo__bar': 'foo', 'bar__foo': 'bar', 'foo':'foobar'}]
        prefix = 'prefix'
        self.assertEqual((['prefix.foo', 'foo.bar', 'bar.foo'], [{'foo.bar': 'foo', 'bar.foo': 'bar', 'prefix.foo': 'foobar'}]), self.housekeeping._lists_normalize(field_list, value_list, prefix))

    def test_045_housekeeping__lists_normalize(self):
        """ test Certificate._fieldlist_normalize() - two values """
        field_list = ['foo', 'foo__bar', 'bar__foo']
        value_list = [{'foo__bar': 'foo1', 'bar__foo': 'bar1', 'foo':'foobar1'}, {'foo__bar': 'foo2', 'bar__foo': 'bar2', 'foo':'foobar2'}]
        prefix = 'prefix'
        result = (['prefix.foo', 'foo.bar', 'bar.foo'], [{'foo.bar': 'foo1', 'bar.foo': 'bar1', 'prefix.foo': 'foobar1'}, {'bar.foo': 'bar2', 'foo.bar': 'foo2', 'prefix.foo': 'foobar2'}])
        self.assertEqual(result, self.housekeeping._lists_normalize(field_list, value_list, prefix))

    def test_046_housekeeping__lists_normalize(self):
        """ test Certificate._fieldlist_normalize() - ele in field list without being in value list """
        field_list = ['foo', 'foo__bar', 'bar__foo']
        value_list = [{'foo__bar': 'foo', 'bar__foo': 'bar'}]
        prefix = 'prefix'
        self.assertEqual((['prefix.foo', 'foo.bar', 'bar.foo'], [{'bar.foo': 'bar', 'foo.bar': 'foo'}]), self.housekeeping._lists_normalize(field_list, value_list, prefix))

    def test_047_housekeeping__lists_normalize(self):
        """ test Certificate._fieldlist_normalize() - ele in value list without being in field list """
        field_list = ['foo__bar']
        value_list = [{'foo__bar': 'foo', 'bar__foo': 'bar'}]
        prefix = 'prefix'
        self.assertEqual((['foo.bar'], [{'foo.bar': 'foo'}]), self.housekeeping._lists_normalize(field_list, value_list, prefix))

    def test_048_housekeeping__accountlist_get(self):
        """ test Housekeeping._accountlist_get - dbstore.accountlist_get() raises an exception  """
        self.housekeeping.dbstore.accountlist_get.side_effect = Exception('exc_house_acc_get')
        with self.assertLogs('test_a2c', level='INFO') as lcm:
            self.housekeeping._accountlist_get()
        self.assertIn('CRITICAL:test_a2c:acme2certifier database error in Housekeeping._accountlist_get(): exc_house_acc_get', lcm.output)

    def test_049_housekeeping__certificatelist_get(self):
        """ test Housekeeping._certificatelist_get - dbstore.certificatelist_get() raises an exception  """
        self.housekeeping.dbstore.certificatelist_get.side_effect = Exception('exc_house_cert_get')
        with self.assertLogs('test_a2c', level='INFO') as lcm:
            self.housekeeping._certificatelist_get()
        self.assertIn('CRITICAL:test_a2c:acme2certifier database error in Housekeeping.certificatelist_get(): exc_house_cert_get', lcm.output)

    def test_050_housekeeping_dbversion_check(self):
        """ test Housekeeping.dbversion_check load  - version match int """
        self.housekeeping.dbstore.dbversion_get.return_value = (1, 'foo')
        with self.assertLogs('test_a2c', level='DEBUG') as lcm:
            self.housekeeping.dbversion_check(1)
        self.assertIn('DEBUG:test_a2c:acme2certifier database version: 1 is upto date', lcm.output)

    def test_051_housekeeping_dbversion_check(self):
        """ test Housekeeping.dbversion_check load  - version match float"""
        self.housekeeping.dbstore.dbversion_get.return_value = (1.0, 'foo')
        with self.assertLogs('test_a2c', level='DEBUG') as lcm:
            self.housekeeping.dbversion_check(1.0)
        self.assertIn('DEBUG:test_a2c:acme2certifier database version: 1.0 is upto date', lcm.output)

    def test_052_housekeeping_dbversion_check(self):
        """ test Housekeeping.dbversion_check load  - version match string"""
        self.housekeeping.dbstore.dbversion_get.return_value = ('1.0-devel', 'foo')
        with self.assertLogs('test_a2c', level='DEBUG') as lcm:
            self.housekeeping.dbversion_check('1.0-devel')
        self.assertIn('DEBUG:test_a2c:acme2certifier database version: 1.0-devel is upto date', lcm.output)

    def test_053_housekeeping_dbversion_check(self):
        """ test Housekeeping.dbversion_check load  - no version number specified """
        # self.signature.dbstore.jwk_load.side_effect = Exception('exc_sig_jw_load')
        with self.assertLogs('test_a2c', level='INFO') as lcm:
            self.housekeeping.dbversion_check()
        self.assertIn('CRITICAL:test_a2c:acme2certifier database version could not be verified in Housekeeping.dbversion_check()', lcm.output)

    def test_054_housekeeping_dbversion_check(self):
        """ test Housekeeping.dbversion_check load - version mismatch """
        self.housekeeping.dbstore.dbversion_get.return_value = (1, 'foo')
        with self.assertLogs('test_a2c', level='INFO') as lcm:
            self.housekeeping.dbversion_check(2)
        self.assertIn('CRITICAL:test_a2c:acme2certifier database version mismatch in: version is 1 but should be 2. Please run the "foo" script', lcm.output)

    def test_055_housekeeping_dbversion_check(self):
        """ test Housekeeping.dbversion_check load - version mismatch """
        self.housekeeping.dbstore.dbversion_get.side_effect =  Exception('exc_dbversion_chk')
        with self.assertLogs('test_a2c', level='INFO') as lcm:
            self.housekeeping.dbversion_check(2)
        self.assertIn('CRITICAL:test_a2c:acme2certifier database error in Housekeeping.dbversion_check(): exc_dbversion_chk', lcm.output)

    @patch('acme.housekeeping.Housekeeping._config_load')
    def test_056__enter__(self, mock_cfg):
        """ test enter """
        mock_cfg.return_value = True
        self.housekeeping.__enter__()
        self.assertTrue(mock_cfg.called)

    @patch('acme.housekeeping.load_config')
    def test_057_config_load(self, mock_load_cfg):
        """ test _config_load empty config """
        parser = configparser.ConfigParser()
        # parser['Account'] = {'foo': 'bar'}
        mock_load_cfg.return_value = parser
        self.housekeeping._config_load()
        self.assertTrue(mock_load_cfg.called)

    @patch('acme.housekeeping.load_config')
    def test_058_config_load(self, mock_load_cfg):
        """ test _config_load empty config """
        parser = configparser.ConfigParser()
        parser['Housekeeping'] = {'foo': 'bar'}
        mock_load_cfg.return_value = parser
        self.housekeeping._config_load()
        self.assertTrue(mock_load_cfg.called)

    @patch('csv.writer')
    @patch("builtins.open", mock_open(read_data='csv_dump'), create=True)
    def test_059__csv_dump(self, mock_write):
        """ test csv dump """
        self.housekeeping._csv_dump('filename', 'data')
        self.assertTrue(mock_write.called)

    @patch('json.dumps')
    @patch("builtins.open", mock_open(read_data='csv_dump'), create=True)
    def test_060__csv_dump(self, mock_json):
        """ test csv dump """
        mock_json.return_value = {'foo': 'bar'}
        self.housekeeping._json_dump('filename', 'data')
        self.assertTrue(mock_json.called)

    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.housekeeping.Housekeeping._accountlist_get')
    def test_061_accountreport_get(self, mock_get, mock_norm, mock_convert):
        """ test accountreport_get() no report name"""
        mock_get.return_value = ('foo', 'bar')
        mock_norm.return_value = ('foo', 'bar')
        mock_convert.return_value = ['list']
        self.assertEqual(['list'], self.housekeeping.accountreport_get('csv', None, False))

    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.housekeeping.Housekeeping._accountlist_get')
    def test_062_accountreport_get(self, mock_get, mock_norm, mock_convert, mock_list, mock_dump):
        """ test accountreport_get() report name csv """
        mock_get.return_value = ('foo', 'bar')
        mock_norm.return_value = ('foo', 'bar')
        mock_convert.return_value = ['list']
        self.assertEqual(['list'], self.housekeeping.accountreport_get('csv', 'report_name', False))
        self.assertTrue(mock_list.called)
        self.assertTrue(mock_dump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._to_acc_json')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.housekeeping.Housekeeping._accountlist_get')
    def test_063_accountreport_get(self, mock_get, mock_norm, mock_convert, mock_list, mock_dump):
        """ test accountreport_get() report name json not nested """
        mock_get.return_value = ('foo', 'bar')
        mock_norm.return_value = ('foo', 'bar')
        mock_convert.return_value = ['list']
        self.assertEqual(['list'], self.housekeeping.accountreport_get('json', 'report_name', False))
        self.assertFalse(mock_list.called)
        self.assertTrue(mock_dump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._to_acc_json')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.housekeeping.Housekeeping._accountlist_get')
    def test_064_accountreport_get(self, mock_get, mock_norm, mock_convert, mock_list, mock_dump):
        """ test accountreport_get() report name json not nested """
        mock_get.return_value = ('foo', 'bar')
        mock_norm.return_value = ('foo', 'bar')
        mock_convert.return_value = ['list']
        mock_list.return_value = ['list1']
        self.assertEqual(['list1'], self.housekeeping.accountreport_get('json', 'report_name', True))
        self.assertTrue(mock_list.called)
        self.assertTrue(mock_dump.called)

    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.housekeeping.Housekeeping._certificatelist_get')
    def test_065_certreport_get(self, mock_get, mock_norm, mock_convert):
        """ test accountreport_get() no report name"""
        mock_get.return_value = ('foo', 'bar')
        mock_norm.return_value = (['foo'], 'bar')
        mock_convert.return_value = ['list']
        self.assertEqual(['list'], self.housekeeping.certreport_get('csv', None))

    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.housekeeping.Housekeeping._certificatelist_get')
    def test_066_certreport_get(self, mock_get, mock_norm, mock_convert, mock_list, mock_dump):
        """ test accountreport_get() no report name"""
        mock_get.return_value = ('foo', 'bar')
        mock_norm.return_value = (['foo'], 'bar')
        mock_convert.return_value = ['list']
        self.assertEqual(['list'], self.housekeeping.certreport_get('csv', 'report_name'))
        self.assertTrue(mock_list.called)
        self.assertTrue(mock_dump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._to_acc_json')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.housekeeping.Housekeeping._certificatelist_get')
    def test_067_certreport_get(self, mock_get, mock_norm, mock_convert, mock_list, mock_dump):
        """ test accountreport_get() report name json not nested """
        mock_get.return_value = ('foo', 'bar')
        mock_norm.return_value = (['foo'], 'bar')
        mock_convert.return_value = ['list']
        self.assertEqual(['list'], self.housekeeping.certreport_get('json', 'report_name'))
        self.assertFalse(mock_list.called)
        self.assertTrue(mock_dump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._to_acc_json')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.housekeeping.Housekeeping._certificatelist_get')
    def test_068_certreport_get(self, mock_get, mock_norm, mock_convert, mock_list, mock_dump):
        """ test accountreport_get() report name json not nested """
        mock_get.return_value = ('foo', 'bar')
        mock_norm.return_value = (['foo'], 'bar')
        mock_convert.return_value = ['list']
        with self.assertLogs('test_a2c', level='INFO') as lcm:
            self.assertEqual(['list'], self.housekeeping.certreport_get('unknown', 'report_name'))
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_dump.called)
        self.assertIn('INFO:test_a2c:Housekeeping.certreport_get(): No dump just return report', lcm.output)

    @patch('acme.certificate.Certificate.dates_update')
    def test_069_certificate_data_update(self, mock_update):
        """ test certificate_dates_update """
        self.housekeeping.certificate_dates_update()
        self.assertTrue(mock_update.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.certificate.Certificate.cleanup')
    @patch('acme.housekeeping.uts_now')
    def test_070_certificates_cleanup(self, mock_uts, mock_cleanup, mock_list, mock_cdump, mock_jdump):
        """ test certificates_cleanup no uts empty report_name """
        mock_uts.return_value = 1111111111
        mock_cleanup.return_value = ('fieldlist', [])
        self.assertFalse(self.housekeeping.certificates_cleanup(uts=None, purge=False, report_format='csv', report_name=None))
        self.assertTrue(mock_uts.called)
        self.assertTrue(mock_cleanup.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.certificate.Certificate.cleanup')
    @patch('acme.housekeeping.uts_now')
    def test_071_certificates_cleanup(self, mock_uts, mock_cleanup, mock_list, mock_cdump, mock_jdump):
        """ test certificates_cleanup no uts empty report_name """
        mock_uts.return_value = 1111111111
        mock_cleanup.return_value = ('fieldlist', [])
        self.assertFalse(self.housekeeping.certificates_cleanup(uts=None, purge=False, report_format='csv', report_name=None))
        self.assertTrue(mock_uts.called)
        self.assertTrue(mock_cleanup.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.certificate.Certificate.cleanup')
    @patch('acme.housekeeping.uts_now')
    def test_072_certificates_cleanup(self, mock_uts, mock_cleanup, mock_list, mock_cdump, mock_jdump):
        """ test certificates_cleanup uts but empty report_name """
        mock_uts.return_value = 1111111111
        mock_cleanup.return_value = ('fieldlist', [])
        self.assertFalse(self.housekeeping.certificates_cleanup(uts='uts', purge=False, report_format='csv', report_name=None))
        self.assertFalse(mock_uts.called)
        self.assertTrue(mock_cleanup.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.certificate.Certificate.cleanup')
    @patch('acme.housekeeping.uts_now')
    def test_073_certificates_cleanup(self, mock_uts, mock_cleanup, mock_list, mock_cdump, mock_jdump):
        """ test certificates_cleanup no uts empty certlist """
        mock_uts.return_value = 111111111
        mock_cleanup.return_value = ('fieldlist', [])
        self.assertFalse(self.housekeeping.certificates_cleanup(uts='foo', purge=False, report_format='csv', report_name='foo'))
        self.assertFalse(mock_uts.called)
        self.assertTrue(mock_cleanup.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.certificate.Certificate.cleanup')
    @patch('acme.housekeeping.uts_now')
    def test_074_certificates_cleanup(self, mock_uts, mock_cleanup, mock_list, mock_cdump, mock_jdump):
        """ test certificates_cleanup csv """
        mock_uts.return_value = 111111111
        mock_cleanup.return_value = ('fieldlist', 'cert_list')
        self.assertEqual('cert_list', self.housekeeping.certificates_cleanup(uts='foo', purge=False, report_format='csv', report_name='foo'))
        self.assertFalse(mock_uts.called)
        self.assertTrue(mock_cleanup.called)
        self.assertTrue(mock_list.called)
        self.assertTrue(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.certificate.Certificate.cleanup')
    @patch('acme.housekeeping.uts_now')
    def test_075_certificates_cleanup(self, mock_uts, mock_cleanup, mock_list, mock_cdump, mock_jdump):
        """ test certificates_cleanup json """
        mock_uts.return_value = 111111111
        mock_cleanup.return_value = ('fieldlist', 'cert_list')
        self.assertEqual('cert_list', self.housekeeping.certificates_cleanup(uts='foo', purge=False, report_format='json', report_name='foo'))
        self.assertFalse(mock_uts.called)
        self.assertTrue(mock_cleanup.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertTrue(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.certificate.Certificate.cleanup')
    @patch('acme.housekeeping.uts_now')
    def test_076_certificates_cleanup(self, mock_uts, mock_cleanup, mock_list, mock_cdump, mock_jdump):
        """ test certificates_cleanup unknown output """
        mock_uts.return_value = 111111111
        mock_cleanup.return_value = ('fieldlist', 'cert_list')
        self.assertEqual('cert_list', self.housekeeping.certificates_cleanup(uts='foo', purge=False, report_format='unkown', report_name='foo'))
        self.assertFalse(mock_uts.called)
        self.assertTrue(mock_cleanup.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.authorization.Authorization.invalidate')
    def test_077_authorizations_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization without report name """
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = 'authorization_list'
        self.housekeeping.authorizations_invalidate(uts='foo', report_format='unkown', report_name=None)
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.authorization.Authorization.invalidate')
    def test_078_authorizations_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization with report name but empty auth_list"""
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = []
        self.housekeeping.authorizations_invalidate(uts='foo', report_format='unkown', report_name='foo')
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.authorization.Authorization.invalidate')
    def test_079_authorizations_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization with report name unknown report format """
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = 'authorization_list'
        self.housekeeping.authorizations_invalidate(uts='foo', report_format='unkown', report_name='foo')
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.authorization.Authorization.invalidate')
    def test_080_authorizations_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization with report name unknown report format """
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = 'authorization_list'
        self.housekeeping.authorizations_invalidate(uts='foo', report_format='csv', report_name='foo')
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertTrue(mock_list.called)
        self.assertTrue(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.authorization.Authorization.invalidate')
    def test_081_authorizations_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization with report name unknown report format """
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = 'authorization_list'
        self.housekeeping.authorizations_invalidate(uts='foo', report_format='json', report_name='foo')
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertTrue(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.order.Order.invalidate')
    def test_082_orders_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization without report name """
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = 'authorization_list'
        self.housekeeping.orders_invalidate(uts='foo', report_format='unkown', report_name=None)
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.order.Order.invalidate')
    def test_083_orders_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization with report name but empty auth_list"""
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = []
        self.housekeeping.orders_invalidate(uts='foo', report_format='unkown', report_name='foo')
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.order.Order.invalidate')
    def test_084_orders_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization with report name unknown report format """
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = 'authorization_list'
        self.housekeeping.orders_invalidate(uts='foo', report_format='unkown', report_name='foo')
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.order.Order.invalidate')
    def test_085_orders_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization with report name unknown report format """
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = 'authorization_list'
        self.housekeeping.orders_invalidate(uts='foo', report_format='csv', report_name='foo')
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertTrue(mock_list.called)
        self.assertTrue(mock_cdump.called)
        self.assertFalse(mock_jdump.called)

    @patch('acme.housekeeping.Housekeeping._json_dump')
    @patch('acme.housekeeping.Housekeeping._csv_dump')
    @patch('acme.housekeeping.Housekeeping._to_list')
    @patch('acme.housekeeping.Housekeeping._convert_data')
    @patch('acme.housekeeping.Housekeeping._lists_normalize')
    @patch('acme.order.Order.invalidate')
    def test_086_orders_invalidate(self, mock_invalidate, mock_normalize, mock_convert, mock_list, mock_cdump, mock_jdump):
        """ authorization with report name unknown report format """
        mock_invalidate.return_value = ('fieldlist', 'cert_list')
        mock_normalize.return_value = ('field_list', 'authorization_list')
        mock_convert.return_value = 'authorization_list'
        self.housekeeping.orders_invalidate(uts='foo', report_format='json', report_name='foo')
        self.assertTrue(mock_invalidate.called)
        self.assertTrue(mock_normalize.called)
        self.assertTrue(mock_convert.called)
        self.assertFalse(mock_list.called)
        self.assertFalse(mock_cdump.called)
        self.assertTrue(mock_jdump.called)

if __name__ == '__main__':
    unittest.main()
