from pyramid.response import Response
from pyramid.config import Configurator
from wsgiref.simple_server import make_server
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import notfound_view_config, view_config
from pyramid.events import NewRequest

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

import utils
import models


@notfound_view_config(append_slash=True)
def notfound(request):
    return HTTPNotFound('Not found')


@view_config(route_name='index')
def index(request):
    return Response('Gateway version %s' % config.get('http_server', 'version'))


@view_config(route_name='ArticlePkg', request_method='GET', renderer="gtw")
def package(request):
    """
    Get a single object and return a serialized dict
    """

    try:
        article = request.db.query(models.ArticlePkg).filter_by(id=request.matchdict['id']).one()
    except NoResultFound:
        return HTTPNotFound()

    return article.to_dict()


@view_config(route_name='list_package', request_method='GET', renderer="gtw")
def list_package(request):
    """
    Return a dict content the total param and the objects list
    Example: {'total': 12, 'limit': 20, offset: 0, 'objects': [object, object,...]}
    """

    limit = request.params.get('limit', config.get('http_server', 'limit'))
    offset = request.params.get('offset', 0)

    articles = request.db.query(models.ArticlePkg).limit(limit).offset(offset)

    return {'limit': limit,
            'offset': offset,
            'total': request.db.query(func.count(models.ArticlePkg.id)).scalar(),
            'objects': [article.to_dict() for article in articles]}


@view_config(route_name='Attempt', request_method='GET', renderer="gtw")
def attempt(request):
    """
    Get a single object and return a serialized dict
    """
    attempt = request.db.query(models.Attempt).filter_by(id=request.matchdict['id']).one()
    if not attempt:
        return HTTPNotFound()

    return attempt.to_dict()


@view_config(route_name='list_attempts', request_method='GET', renderer="gtw")
def attempts(request):
    """
    Return a dict content the total param and the objects list
    Example: {'total': 12, 'limit': 20, offset:0, 'objects': [object, object,...]}
    """
    limit = request.params.get('limit', config.get('http_server', 'limit'))
    offset = request.params.get('offset', 0)

    attempts = request.db.query(models.Attempt).limit(limit).offset(offset)

    return {'limit': limit,
            'offset': offset,
            'total': request.db.query(func.count(models.Attempt.id)).scalar(),
            'objects': [attempt.to_dict() for attempt in attempts]}


if __name__ == '__main__':

    def bind_db(event):
        event.request.db = event.request.registry.Session()

    #Database configurator
    config = utils.Configuration.from_env()
    engine = models.create_engine_from_config(config)

    config_pyrmd = Configurator()
    config_pyrmd.add_route('index', '/')

    config_pyrmd.add_route('ArticlePkg',
        '/api/%s/packages/{id}/' % config.get('http_server', 'version'))
    config_pyrmd.add_route('Attempt',
        '/api/%s/attempts/{id}/' % config.get('http_server', 'version'))
    config_pyrmd.add_route('list_package',
        '/api/%s/packages/' % config.get('http_server', 'version'))
    config_pyrmd.add_route('list_attempts',
        '/api/%s/attempts/' % config.get('http_server', 'version'))

    config_pyrmd.add_renderer('gtw', factory='renderers.GtwFactory')

    #DB session bound to each request
    config_pyrmd.registry.Session = models.Session
    config_pyrmd.registry.Session.configure(bind=engine)
    config_pyrmd.add_subscriber(bind_db, NewRequest)

    config_pyrmd.scan()

    app = config_pyrmd.make_wsgi_app()

    server = make_server(config.get('http_server', 'ip'), config.getint('http_server', 'port'), app)
    server.serve_forever()
