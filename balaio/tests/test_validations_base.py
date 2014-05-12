import unittest

import mocker

from balaio.lib.validations import base
from balaio.lib import models, utils
from balaio.tests.doubles import *


class ValidationPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda args: NotifierStub)

        vpipe = base.ValidationPipe(notifier=_notifier)
        vpipe.feed(data)
        return vpipe

    def test_notifier_isnt_called_during_initialization(self):
        mock_notifier = self.mocker.mock()
        mock_scieloapi = self.mocker.mock()
        self.mocker.replay()

        vpipe = self._makeOne([{'name': 'foo'}], _notifier=mock_notifier)

        self.assertIsInstance(vpipe, base.ValidationPipe)

    def test_transform_calls_validate_stage_notifier(self):
        """
        Asserts that methods expected to be defined by the subclasses are being called.
        """
        base.ValidationPipe._notifier = NotifierStub()
        mock_self = self.mocker.mock(base.ValidationPipe)

        item = [AttemptStub(), ArticlePkgStub(), {}, SessionStub()]

        mock_self.validate(item)
        self.mocker.result([models.Status.ok, 'foo'])

        mock_self._stage_
        self.mocker.result('bar')

        mock_self._notifier(item[0], item[3])
        self.mocker.result(NotifierStub())

        self.mocker.replay()

        self.assertEqual(
            base.ValidationPipe.transform(mock_self, item),
            item)

    def test_validate_raises_NotImplementedError(self):
        vpipe = self._makeOne([{'name': 'foo'}])
        self.assertRaises(NotImplementedError, lambda: vpipe.validate('foo'))


class SetupPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        _scieloapi = kwargs.get('_scieloapi', ScieloAPIClientStub())
        _notifier = kwargs.get('_notifier', lambda args: NotifierStub)
        _sapi_tools = kwargs.get('_sapi_tools', get_ScieloAPIToolbeltStubModule())
        _pkg_analyzer = kwargs.get('_pkg_analyzer', PackageAnalyzerStub)
        _issn_validator = kwargs.get('_issn_validator', utils.is_valid_issn)

        vpipe = base.SetupPipe(scieloapi=_scieloapi,
                               notifier=_notifier,
                               sapi_tools=_sapi_tools,
                               pkg_analyzer=_pkg_analyzer,
                               issn_validator=_issn_validator)
        vpipe.feed(data)
        return vpipe

    def test_get_journal_1(self):
        """
        Call `_fetch_journal_and_issue_data` function with only `print_issn`
        as search criteria.
        """
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        scieloapi = ScieloAPIClientStub()

        mock_func = self.mocker.mock()
        mock_func(print_issn='0100-879X')
        self.mocker.result({'foo': 'bar'})  # this is the meaningful part of the test

        self.mocker.replay()

        vpipe = self._makeOne(data, _scieloapi=scieloapi)
        vpipe._fetch_journal_and_issue_data = mock_func

        attempt = AttemptStub()
        attempt.articlepkg.issue_volume = None
        attempt.articlepkg.issue_number = None
        attempt.articlepkg.issue_suppl_volume = None
        attempt.articlepkg.issue_suppl_number = None
        attempt.articlepkg.journal_pissn = '0100-879X'
        attempt.articlepkg.journal_eissn = None

        self.assertEqual(vpipe.get_journal(attempt), {'foo': 'bar'})

    def test_get_journal_2(self):
        """
        Call `_fetch_journal_and_issue_data` function with `print_issn`
        and article data as search criteria.
        """
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        scieloapi = ScieloAPIClientStub()

        mock_func = self.mocker.mock()
        mock_func(print_issn='0100-879X', volume='1', number='2',
            suppl_volume='1', suppl_number='2')
        self.mocker.result({'foo': 'bar'})  # this is the meaningful part of the test

        self.mocker.replay()

        vpipe = self._makeOne(data, _scieloapi=scieloapi)
        vpipe._fetch_journal_and_issue_data = mock_func

        attempt = AttemptStub()
        attempt.articlepkg.issue_volume = '1'
        attempt.articlepkg.issue_number = '2'
        attempt.articlepkg.issue_suppl_volume = '1'
        attempt.articlepkg.issue_suppl_number = '2'
        attempt.articlepkg.journal_pissn = '0100-879X'
        attempt.articlepkg.journal_eissn = None

        self.assertEqual(vpipe.get_journal(attempt), {'foo': 'bar'})

    def test_get_journal_3(self):
        """
        Call `_fetch_journal_and_issue_data` function with only `electronic_issn`
        as search criteria.
        """
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        scieloapi = ScieloAPIClientStub()

        mock_func = self.mocker.mock()
        mock_func(eletronic_issn='0100-879X')
        self.mocker.result({'foo': 'bar'})  # this is the meaningful part of the test

        self.mocker.replay()

        vpipe = self._makeOne(data, _scieloapi=scieloapi)
        vpipe._fetch_journal_and_issue_data = mock_func

        attempt = AttemptStub()
        attempt.articlepkg.issue_volume = None
        attempt.articlepkg.issue_number = None
        attempt.articlepkg.issue_suppl_volume = None
        attempt.articlepkg.issue_suppl_number = None
        attempt.articlepkg.journal_pissn = None
        attempt.articlepkg.journal_eissn = '0100-879X'

        self.assertEqual(vpipe.get_journal(attempt), {'foo': 'bar'})

    def test_get_journal_4(self):
        """
        Call `_fetch_journal_and_issue_data` function with `electronic_issn`
        and article data as search criteria.
        """
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        scieloapi = ScieloAPIClientStub()

        mock_func = self.mocker.mock()
        mock_func(eletronic_issn='0100-879X', volume='1', number='2',
            suppl_volume='1', suppl_number='2')
        self.mocker.result({'foo': 'bar'})  # this is the meaningful part of the test

        self.mocker.replay()

        vpipe = self._makeOne(data, _scieloapi=scieloapi)
        vpipe._fetch_journal_and_issue_data = mock_func

        attempt = AttemptStub()
        attempt.articlepkg.issue_volume = '1'
        attempt.articlepkg.issue_number = '2'
        attempt.articlepkg.issue_suppl_volume = '1'
        attempt.articlepkg.issue_suppl_number = '2'
        attempt.articlepkg.journal_pissn = None
        attempt.articlepkg.journal_eissn = '0100-879X'

        self.assertEqual(vpipe.get_journal(attempt), {'foo': 'bar'})

    def test_transform_returns_right_datastructure(self):
        """
        The right datastructure is a tuple in the form:
        (<models.Attempt>, <checkin.PackageAnalyzer>, <dict>, Session)
        """
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        scieloapi = ScieloAPIClientStub()
        scieloapi.issues.filter = lambda print_issn=None, eletronic_issn=None, \
            volume=None, number=None, suppl_volume=None, suppl_number=None, limit=None: [{}]

        vpipe = self._makeOne(data, _scieloapi=scieloapi)
        vpipe._notifier = lambda a, b: NotifierStub()
        result = vpipe.transform((AttemptStub(), SessionStub()))

        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result[0], AttemptStub)
        self.assertIsInstance(result[1], PackageAnalyzerStub)
        # index 2 is the return data from scieloapi.journals.filter
        # so, testing its type actualy means nothing.
        self.assertEqual(len(result), 4)

    def test_fetch_journal_issue_data_with_valid_criteria(self):
        """
        Valid criteria means a valid querystring param.
        See a list at http://ref.scielo.org/nssk38

        The behaviour defined by the Restful API is to
        ignore the query for invalid criteria, and so
        do we.
        """
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"
        scieloapi = ScieloAPIClientStub()
        scieloapi.issues.filter = lambda **kwargs: [{'foo': 'bar'}]

        vpipe = self._makeOne(data, _scieloapi=scieloapi)
        self.assertEqual(vpipe._fetch_journal_and_issue_data(print_issn='0100-879X', **{'volume': '30', 'number': '4'}),
                         {'foo': 'bar'})

    def test_fetch_journal_issue_data_with_unknown_issn_raises_ValueError(self):
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"
        scieloapi = ScieloAPIClientStub()
        scieloapi.journals.filter = lambda **kwargs: []

        sapi_tools = get_ScieloAPIToolbeltStubModule()

        def _get_one(dataset):
            raise ValueError()
        sapi_tools.get_one = _get_one

        vpipe = self._makeOne(data, _scieloapi=scieloapi, _sapi_tools=sapi_tools)
        self.assertIsNone(vpipe._fetch_journal_and_issue_data(print_issn='0100-879X',
            **{'volume': '30', 'number': '4'}))

    def test_fetch_journal_issue_data_with_unknown_criteria(self):
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"
        scieloapi = ScieloAPIClientStub()
        scieloapi.journals.filter = lambda **kwargs: []

        sapi_tools = get_ScieloAPIToolbeltStubModule()

        def _get_one(dataset):
            raise ValueError()
        sapi_tools.get_one = _get_one

        vpipe = self._makeOne(data, _scieloapi=scieloapi, _sapi_tools=sapi_tools)
        self.assertIsNone(vpipe._fetch_journal_and_issue_data(
            **{'print_issn': '1234-1234', 'volume': '30', 'number': '4'}))

    def test_transform_grants_valid_issn_before_fetching(self):
        #FIXME verificar
        stub_attempt = AttemptStub()
        stub_attempt.articlepkg.journal_pissn = '0100-879X'
        stub_attempt.articlepkg.journal_eissn = None
        stub_attempt.articlepkg.issue_volume = '30'
        stub_attempt.articlepkg.issue_number = '4'

        mock_issn_validator = self.mocker.mock()
        #mock_fetch_journal_data = self.mocker.mock()
        mock_fetch_journal_and_issue_data = self.mocker.mock()

        with self.mocker.order():
            mock_issn_validator('0100-879X')
            self.mocker.result(True)

            #mock_fetch_journal_data({'print_issn': '0100-879X'})
            #self.mocker.result({'foo': 'bar', 'resource_uri': '/api/...'})

            mock_fetch_journal_and_issue_data(print_issn='0100-879X', **{'volume': '30', 'number': '4'})
            self.mocker.result({'foo': 'bar'})

            self.mocker.replay()

        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        vpipe = self._makeOne(data)
        vpipe._issn_validator = mock_issn_validator
        #vpipe._fetch_journal_data = mock_fetch_journal_data
        vpipe._fetch_journal_and_issue_data = mock_fetch_journal_and_issue_data
        vpipe._notifier = lambda a, b: NotifierStub()

        result = vpipe.transform((stub_attempt, SessionStub()))

