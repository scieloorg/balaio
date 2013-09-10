from pyramid.response import Response
from pyramid.config import Configurator
from wsgiref.simple_server import make_server
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import notfound_view_config, view_config

from sqlalchemy.orm.exc import NoResultFound

import utils
import models

__version__ = "v1"

config = utils.Configuration.from_env()

Session = models.Session

Session.configure(bind=models.create_engine_from_config(config))


@notfound_view_config(append_slash=True)
def notfound(request):
    return HTTPNotFound('Not found')


@view_config(route_name='index')
def index(request):

    return Response('Gateway version %s' % __version__)


@view_config(route_name='package', request_method='GET', renderer="gtw")
def package(request):

    session = Session()

    try:
        article = session.query(models.ArticlePkg).filter_by(id=request.matchdict['id']).one()
    except NoResultFound:
        return HTTPNotFound()

    return article.to_dict()


@view_config(route_name='list_package', request_method='GET', renderer="gtw")
def list_package(request):
    session = Session()

    limit = request.params.get('limit', 20)
    offset = request.params.get('offset', 0)

    articles = session.query(models.ArticlePkg).limit(limit).offset(offset)

    return [article.to_dict() for article in articles]


if __name__ == '__main__':
    config = Configurator()
    config.add_route('index', '/')

    config.add_route('list_package', '/api/%s/packages/' % __version__)
    config.add_route('package', '/api/%s/packages/{id}' % __version__)

    #Gateway renderer
    config.add_renderer('gtw', factory='renderers.GtwFactory')

    config.scan()

    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
