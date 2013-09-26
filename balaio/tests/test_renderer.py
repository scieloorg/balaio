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

    def test_new_offset_for_previous_20_0(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._new_offset(offset=20, limit=20), 0)

    def test_new_offset_for_previous_0_None(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._new_offset(offset=0, limit=20), None)

    def test_new_offset_for_previous_50_0(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._new_offset(offset=50, limit=50), 0)

    def test_new_offset_for_previous_50_None(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._new_offset(offset=0, limit=50), None)

    def test_new_offset_for_next_0_41_20(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._new_offset(offset=0, limit=20, total_count=41), 20)

    def test_new_offset_for_next_20_41_40(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._new_offset(offset=20, limit=20, total_count=41), 40)

    def test_new_offset_for_next_20_40_None(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._new_offset(offset=20, limit=20, total_count=40), None)

    def test_new_offset_for_next_20_39_None(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._new_offset(offset=20, limit=20, total_count=39), None)

    def test_new_offset_for_next_40_39_None(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._new_offset(offset=40, limit=20, total_count=39), None)

    def test_next_resource_uri(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(
            renderer._navigation(100, 20, 200),
            "/api/v1/attempts/?limit=20&offset=120"
        )

    def test_next_resource_uri_80_90(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(
            renderer._navigation(80, 20, 90),
            None
        )

    def test_previous_resource_uri(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(
            renderer._navigation(100, 20),
            "/api/v1/attempts/?limit=20&offset=80"
        )

    def test_next_resource_uri_is_None(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(
            renderer._navigation(180, 20, 200),
            None
        )

    def test_previous_resource_uri_is_None(self):
        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req
        self.assertEqual(
            renderer._navigation(0, 20),
            None
        )

    def test_add_meta_without_reference_list(self):
        data = {'limit': 20,
                'offset': 0,
                'total': 200,
                'objects': [AttemptStub().to_dict()]
                }

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
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
                'objects': [ArticlePkgStub().to_dict()]}

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/packages/"
        self.config.add_route('Attempt', '/api/v1/attempts/{id}/')

        renderer.request = self.req

        self.assertEqual(renderer.add_meta(data), {
                'meta':
                    {
                        'total_count': 200,
                        'limit': 20,
                        'offset': 0,
                        'next': '/api/v1/packages/?limit=20&offset=20',
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
