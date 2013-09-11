from pyramid.response import Response
from pyramid.config import Configurator
from wsgiref.simple_server import make_server
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import notfound_view_config, view_config

from sqlalchemy.orm.exc import NoResultFound

import utils
import models

from models import(
    Session,
    Base,)

__limit__ = 20

__version__ = "v1"

session = Session()


@notfound_view_config(append_slash=True)
def notfound(request):
    return HTTPNotFound('Not found')


@view_config(route_name='index')
def index(request):
    return Response('Gateway version %s' % __version__)


@view_config(route_name='package', request_method='GET', renderer="gtw")
def package(request):
    """
    Get a single object and return a serialized dict
    """

    try:
        article = session.query(models.ArticlePkg).filter_by(id=request.matchdict['id']).one()
    except NoResultFound:
        return HTTPNotFound()

    return article.to_dict()


@view_config(route_name='list_package', request_method='GET', renderer="gtw")
def list_package(request):
    """
    Return a dict content the total param and the objects list
    Example: {'total': 12, 'limit': 20, offset: 0, 'objects': [object, object,...]}
    """

    limit = request.params.get('limit', __limit__)
    offset = request.params.get('offset', 0)

    articles = session.query(models.ArticlePkg).limit(limit).offset(offset)

    return {'limit': limit,
            'offset': offset,
            'total': session.query(models.ArticlePkg).count(),
            'objects': [article.to_dict() for article in articles]}


@view_config(route_name='attempt', request_method='GET', renderer="gtw")
def attempt(request):
    """
    Get a single object and return a serialized dict
    """
    session = Session()

    try:
        article = session.query(models.Attempt).filter_by(id=request.matchdict['id']).one()
    except NoResultFound:
        return HTTPNotFound()

    return article.to_dict()


@view_config(route_name='attempts', request_method='GET', renderer="gtw")
def list_attempt(request):
    """
    Return a dict content the total param and the objects list
    Example: {'total': 12, 'limit': 20, offset:0, 'objects': [object, object,...]}
    """
    session = Session()

    limit = request.params.get('limit', __limit__)
    offset = request.params.get('offset', 0)

    articles = session.query(models.Attempt).limit(limit).offset(offset)

    return {'limit': limit,
            'offset': offset,
            'total': session.query(models.Attempt).count(),
            'objects': [article.to_dict() for article in articles]}


if __name__ == '__main__':
    #Database configurator
    config = utils.Configuration.from_env()
    engine = models.create_engine_from_config(config)
    Session.configure(bind=engine)
    Base.metadata.bind = engine

    config = Configurator()
    config.add_route('index', '/')

    config.add_route('list_package', '/api/%s/packages/' % __version__)
    config.add_route('package', '/api/%s/packages/{id}' % __version__)
    config.add_route('attempts', '/api/%s/attempts/' % __version__)
    config.add_route('attempt', '/api/%s/attempts/{id}' % __version__)

    #Gateway renderer
    config.add_renderer('gtw', factory='renderers.GtwFactory')

    config.scan()

    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
