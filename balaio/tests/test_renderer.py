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

    def test_format_response_for_a_single_object(self):
        data = AttemptStub().to_dict()
        expected = data
        expected['resource_uri'] = '/api/v1/attempts/1/'

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/1/"
        renderer.request = self.req

        self.assertEqual(renderer.add_meta(data), {
                'meta':
                    {
                        'total': 200,
                        'limit': 20,
                        'offset': 0
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

    def test_format_response_for_a_list_of_objects(self):

        data = {'limit': 20,
                'offset': 0,
                'total': 200,
                'objects': [ArticlePkgStub().to_dict()]}

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/packages/"
        self.config.add_route('Attempt', '/api/v1/attempts/{id}/')
        self.config.add_route('Ticket', '/api/v1/tickets/{id}/')

        renderer.request = self.req

        self.assertEqual(renderer.format_response(data), {
                'meta':
                    {
                        'total': 200,
                        'limit': 20,
                        'offset': 0
                    },
                'objects':
                    [
                        {
                            'journal_pissn': '0100-879X',
                            'journal_eissn': '0100-879X',
                            'issue_suppl_number': None,
                            'attempts':
                                [
                                    '/api/v1/attempts/1/',
                                    '/api/v1/attempts/2/'
                                ],
                            'issue_suppl_volume': None,
                            'issue_volume': '31',
                            'resource_uri': '/api/v1/packages/1/',
                            'id': 1,
                            'issue_number': '1',
                            'tickets': ['/api/v1/tickets/11/',
                                    '/api/v1/tickets/12/']
                        }
                    ]})

    def test_add_resource_without_related_resources(self):
        data = {
                    'collection_uri': '/api/v1/collection/xxx/',
                    'filepath': '/tmp/foo/bar.zip',
                    'finished_at': None,
                    'articlepkg_id': 1,
                    'is_valid': True,
                    'started_at': '2013-09-18 14:11:04.129956',
                    'id': 1,
                    'package_checksum': 'ol9j27n3f52kne7hbn',
                    
                }

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req

        self.assertEqual(renderer.add_resource_uri(data), 
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
                })

    def test_add_resource_to_object_which_has_related_resources(self):
        data = ArticlePkgStub().to_dict()

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/packages/"
        self.config.add_route('Attempt', '/api/v1/attempts/{id}/')
        self.config.add_route('Ticket', '/api/v1/tickets/{id}/')

        renderer.request = self.req

        self.assertEqual(renderer.format_response(data), 
                {
                    'journal_pissn': '0100-879X',
                    'journal_eissn': '0100-879X',
                    'issue_suppl_number': None,
                    'attempts':
                        [
                            '/api/v1/attempts/1/',
                            '/api/v1/attempts/2/'
                        ],
                    'issue_suppl_volume': None,
                    'issue_volume': '31',
                    'resource_uri': '/api/v1/packages/1/',
                    'id': 1,
                    'issue_number': '1',
                    'tickets': [
                            '/api/v1/tickets/11/',
                            '/api/v1/tickets/12/']
                })
