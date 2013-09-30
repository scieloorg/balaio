import unittest
from pyramid import testing
from balaio.renderers import GtwMetaFactory
from balaio.tests.doubles import *


class TestRenderer(unittest.TestCase):

    def setUp(self):
        self.req = testing.DummyRequest()
        self.config = testing.setUp(request=self.req)

    def tearDown(self):
        testing.tearDown()

    def test_int_None(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int(None), 0)

    def test_int(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int(10), 10)

    def test_int_string_zero_len(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int(''), 0)

    def test_int_string(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int('10'), 10)

    def test_int_string_negative(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int('-10'), 0)

    def test_int_negative(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int(-10), 0)

    def test_int_string_not_number(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int('bla'), 0)

    def test_previous_offset_offset_None_limit_None(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._prev_offset(offset=0, limit=None), None)

    def test_previous_offset_offset_None_limit_20(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._prev_offset(offset=20, limit=None), 0)

    def test_previous_offset_offset_0_limit_None(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._prev_offset(offset=0, limit=None), None)

    def test_previous_offset_offset_0_limit_20(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._prev_offset(offset=0, limit=20), None)

    def test_previous_offset_offset_20_limit_None(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._prev_offset(offset=20, limit=None), 0)

    def test_previous_offset_offset_20_limit_20(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._prev_offset(offset=20, limit=20), 0)

    def test_next_offset_offset_None_limit_None(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._next_offset(offset=None, limit=None, total=100), 20)

    def test_next_offset_offset_None_limit_40(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._next_offset(offset=None, limit=40, total=100), 40)

    def test_next_offset_offset_50_limit_50(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._next_offset(offset=50, limit=50, total=101), 100)

    def test_next_offset_offset_20_limit_20_total_39(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._next_offset(offset=20, limit=20, total=39), None)

    def test_next_offset_offset_20_limit_20_total_40(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._next_offset(offset=20, limit=20, total=40), 40)

    def test_next_offset_offset_20_limit_20_total_41(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(renderer._next_offset(offset=20, limit=20, total=41), 40)

    def test_add_meta_without_reference_list(self):
        data = {'limit': 20,
                'offset': 0,
                'total': 200,
                'objects': [AttemptStub().to_dict()]
                }
        self.req.path = "/api/v1/attempts/"
        self.config.add_route('list_attempt', '/api/v1/attempts/')

        renderer = GtwMetaFactory()
        renderer.request = self.req

        self.assertEqual(renderer.add_meta(data), {
                'meta':
                    {
                        'total_count': 200,
                        'limit': 20,
                        'offset': 0,
                        'previous': None,
                        'next': '/api/v1/attempts/?limit=20&offset=20',
                        
                    },
                'objects':
                    [
                        {
                            'collection_uri': '/api/v1/collection/xxx/',
                            'filepath': '/tmp/foo/bar.zip',
                            'finished_at': None,
                            'articlepkg_id': 1,
                            'is_valid': True,
                            'started_at': '2013-09-18 14:11:04.129956',
                            'id': 1,
                            'package_checksum': 'ol9j27n3f52kne7hbn',
                            'resource_uri': '/api/v1/attempts/1/'
                        }
                       ]})

    def test_add_meta_with_reference_list(self):

        data = {'limit': 20,
                'offset': 0,
                'total': 200,
                'filters': {'journal_pissn': '0100-879X'},
                'objects': [ArticlePkgStub().to_dict()]}

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/packages/"
        self.config.add_route('list_package', '/api/v1/packages/')
        self.config.add_route('list_attempt', '/api/v1/attempts/')
        self.config.add_route('Attempt', '/api/v1/attempts/{id}/')

        renderer.request = self.req

        self.assertEqual(renderer.add_meta(data), {
                'meta':
                    {
                        'total_count': 200,
                        'limit': 20,
                        'offset': 0,
                        'next': '/api/v1/packages/?journal_pissn=0100-879X&limit=20&offset=20',
                        'previous': None,
                    },
                'objects':
                    [
                        {
                            'journal_pissn': '0100-879X',
                            'journal_eissn': '0100-879X',
                            'issue_suppl_number': None,
                            'attempts':
                                [
                                    '/api/v1/attempts/1/'
                                ],
                            'issue_suppl_volume': None,
                            'issue_volume': '31',
                            'resource_uri': '/api/v1/packages/1/',
                            'id': 1,
                            'issue_number': '1'
                        }
                    ]})

    def test_add_resource_without_reference_list(self):
        data = [AttemptStub().to_dict()]

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req

        self.assertEqual(renderer.add_resource_uri(data), [
                {
                    'collection_uri': '/api/v1/collection/xxx/',
                    'filepath': '/tmp/foo/bar.zip',
                    'finished_at': None,
                    'articlepkg_id': 1,
                    'is_valid': True,
                    'started_at': '2013-09-18 14:11:04.129956',
                    'id': 1,
                    'package_checksum': 'ol9j27n3f52kne7hbn',
                    'resource_uri':'/api/v1/attempts/1/'
                }])

    def test_add_resource_with_reference_list(self):
        data = [ArticlePkgStub().to_dict()]

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/packages/"
        self.config.add_route('Attempt', '/api/v1/attempts/{id}/')

        renderer.request = self.req

        self.assertEqual(renderer.add_meta(data), [
                {
                    'journal_pissn': '0100-879X',
                    'journal_eissn': '0100-879X',
                    'issue_suppl_number': None,
                    'attempts':
                        [
                            '/api/v1/attempts/1/'
                        ],
                    'issue_suppl_volume': None,
                    'issue_volume': '31',
                    'resource_uri': '/api/v1/packages/1/',
                    'id': 1,
                    'issue_number': '1'
                }])

    def test_translate_ref_without_itens(self):
        data = []

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/packages/"
        self.config.add_route('Attempt', '/api/v1/attempts/{id}/')

        renderer.request = self.req

        self.assertEqual(renderer.translate_ref(data), [])

    def test_translate_ref(self):
        data = [['Attempt', '1'], ['Attempt', '2'], ['Attempt', '3']]

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/packages/"
        self.config.add_route('Attempt', '/api/v1/attempts/{id}/')

        renderer.request = self.req

        self.assertEqual(renderer.translate_ref(data), ['/api/v1/attempts/1/',
            '/api/v1/attempts/2/', '/api/v1/attempts/3/'])
