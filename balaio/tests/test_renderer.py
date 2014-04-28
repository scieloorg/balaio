import unittest
from pyramid import testing
from balaio.lib.renderers import GtwMetaFactory
from balaio.tests.doubles import *


class TestRenderer(unittest.TestCase):

    def setUp(self):
        self.req = testing.DummyRequest()
        self.config = testing.setUp(request=self.req)

    def tearDown(self):
        testing.tearDown()

    def test_positive_int_or_zero_None(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int_or_zero(None), 0)

    def test_int(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int_or_zero(10), 10)

    def test_positive_int_or_zero_string_zero_len(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int_or_zero(''), 0)

    def test_positive_int_or_zero_string(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int_or_zero('10'), 10)

    def test_positive_int_or_zero_string_negative(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int_or_zero('-10'), 0)

    def test_positive_int_or_zero_negative(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int_or_zero(-10), 0)

    def test_positive_int_or_zero_string_not_number(self):
        renderer = GtwMetaFactory()
        self.assertEqual(renderer._positive_int_or_zero('bla'), 0)

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

    def test_current_resource_path(self):
        from pyramid.interfaces import IRoutesMapper
        route = DummyRoute('/1/2/3')
        mapper = DummyRoutesMapper(route=route)
        self.req.matched_route = route
        self.req.matchdict = {}
        self.req.script_name = '/script_name'
        self.req.registry.registerUtility(mapper, IRoutesMapper)

        renderer = GtwMetaFactory()
        renderer.request = self.req
        result = renderer._current_resource_path({'foo': 'bar'}, limit=15, offset=50)

        self.assertEqual(result, '/script_name/1/2/3?foo=bar&limit=15&offset=50')

    def test_format_response_for_a_single_object(self):
        data = AttemptStub().to_dict()
        expected = data
        expected['resource_uri'] = '/api/v1/attempts/1/'

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/1/"
        renderer.request = self.req

        self.assertEqual(renderer.format_response(data),
                        expected
                       )

    def test_format_response_for_a_list_of_objects(self):

        data = {'limit': 20,
                'offset': 0,
                'total': 200,
                'objects': [{'id':1, 'data':1}]}

        self.req.path = "/api/v1/packages/"
        self.config.add_route('Attempt', '/api/v1/attempts/{id}/')
        self.config.add_route('Ticket', '/api/v1/tickets/{id}/')

        renderer = GtwMetaFactory()
        renderer.request = self.req
        renderer._current_resource_path = lambda *args, **kwargs: self.req.path + '?limit=20&offset=20'

        self.assertEqual(renderer.format_response(data), {
                'meta':{
                        'total': 200,
                        'limit': 20,
                        'offset': 0,
                        'next': "/api/v1/packages/?limit=20&offset=20",
                        'previous': None,
                        },
                'objects':
                    [
                        {'id':1,
                            'data':1,
                            'resource_uri': '/api/v1/packages/1/'
                        }
                    ]
                    })

    def test_add_resource_to_object_without_related_resources(self):
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
        expected = {'resource_uri': '/api/v1/attempts/1/'}
        expected.update(data)

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/attempts/"
        renderer.request = self.req

        self.assertEqual(renderer.add_resource_uri(data), expected)

    def test_add_resource_to_object_which_has_related_resources(self):
        data = ArticlePkgStub().to_dict()
        expected = {}
        expected.update(data)
        expected.update({'tickets':  ['/api/v1/tickets/11/', '/api/v1/tickets/12/']})
        expected.update({'attempts': ['/api/v1/attempts/1/', '/api/v1/attempts/2/']})
        expected.update({'resource_uri': '/api/v1/packages/1/'})
        del expected['related_resources']

        renderer = GtwMetaFactory()
        self.req.path = "/api/v1/packages/"
        self.config.add_route('Attempt', '/api/v1/attempts/{id}/')
        self.config.add_route('Ticket', '/api/v1/tickets/{id}/')

        renderer.request = self.req
        renderer._current_resource_path = lambda *args, **kwargs: None

        self.assertEqual(renderer.add_resource_uri(data), expected)

