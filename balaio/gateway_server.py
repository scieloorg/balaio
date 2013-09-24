from pyramid.response import Response
from pyramid.config import Configurator
from wsgiref.simple_server import make_server
from pyramid.httpexceptions import HTTPNotFound, HTTPAccepted, HTTPCreated
from pyramid.view import notfound_view_config, view_config
from pyramid.events import NewRequest

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

import utils
import models


def get_query_filters(model, request_params):
    filters = {}
    for name, value in request_params.items():
        if hasattr(model, name):
            filters[name] = value
    return filters


@notfound_view_config(append_slash=True)
def notfound(request):
    return HTTPNotFound('Not found')


@view_config(route_name='index')
def index(request):
    return Response('Gateway version %s' % request.registry.settings['http_server']['version'])


@view_config(route_name='ArticlePkg', request_method='GET', renderer="gtw")
def package(request):
    """
    Get a single object and return a serialized dict
    """

    article = request.db.query(models.ArticlePkg).get(request.matchdict['id'])

    if article is None:
        return HTTPNotFound()

    return article.to_dict()


@view_config(route_name='list_package', request_method='GET', renderer="gtw")
def list_package(request):
    """
    Return a dict content the total param and the objects list
    Example: {'total': 12, 'limit': 20, offset: 0, 'objects': [object, object,...]}
    """
    limit = request.params.get('limit', request.registry.settings.get('http_server', {}).get('limit', 20))
    offset = request.params.get('offset', 0)

    filters = get_query_filters(models.ArticlePkg, request.params)
    articles = request.db.query(models.ArticlePkg).filter_by(**filters).limit(limit).offset(offset)

    return {'limit': limit,
            'offset': offset,
            'total': request.db.query(func.count(models.ArticlePkg.id)).scalar(),
            'objects': [article.to_dict() for article in articles]}


@view_config(route_name='Attempt', request_method='GET', renderer="gtw")
def attempt(request):
    """
    Get a single object and return a serialized dict
    """
    attempt = request.db.query(models.Attempt).get(request.matchdict['id'])

    if not attempt:
        return HTTPNotFound()

    return attempt.to_dict()


@view_config(route_name='list_attempts', request_method='GET', renderer="gtw")
def attempts(request):
    """
    Return a dict content the total param and the objects list
    Example: {'total': 12, 'limit': 20, offset:0, 'objects': [object, object,...]}
    """
    limit = request.params.get('limit', request.registry.settings.get('http_server', {}).get('limit', 20))
    offset = request.params.get('offset', 0)

    filters = get_query_filters(models.Attempt, request.params)
    attempts = request.db.query(models.Attempt).filter_by(**filters).limit(limit).offset(offset)

    return {'limit': limit,
            'offset': offset,
            'total': request.db.query(func.count(models.Attempt.id)).scalar(),
            'objects': [attempt.to_dict() for attempt in attempts]}


@view_config(route_name='Ticket', request_method='GET', renderer="gtw")
def ticket(request):
    """
    Get a single object and return a serialized dict
    """

    ticket = request.db.query(models.Ticket).get(request.matchdict['id'])

    if ticket is None:
        return HTTPNotFound()

    return ticket.to_dict()


@view_config(route_name='list_ticket', request_method='GET', renderer="gtw")
def list_ticket(request):
    """
    Return a dict content the total param and the objects list
    Example: {'total': 12, 'limit': 20, offset: 0, 'objects': [object, object,...]}
    """

    limit = request.params.get('limit', request.registry.settings.get('http_server', {}).get('limit', 20))
    offset = request.params.get('offset', 0)
    filters = get_query_filters(models.Ticket, request.params)
    tickets = request.db.query(models.Ticket).filter_by(**filters).limit(limit).offset(offset)

    return {'limit': limit,
            'offset': offset,
            'total': request.db.query(func.count(models.Ticket.id)).scalar(),
            'objects': [ticket.to_dict() for ticket in tickets]}


@view_config(route_name='new_ticket', request_method='POST', renderer="gtw")
def new_ticket(request):
    """
    Creates a ticket with or without comment.
    Returns the new ticket as a serialized dict
    """
    ticket = models.Ticket(articlepkg_id=request.POST['articlepkg_id'], author=request.POST['ticket_author'], title=request.POST['title'])
    if request.POST.get('message', None):
        ticket.comments.append(models.Comment(author=request.POST['ticket_author'], message=request.POST['message']))
    try:
        request.db.add(ticket)
        request.db.commit()
    except:
        request.db.rollback()
        raise

    return HTTPCreated()


@view_config(route_name='update_ticket', request_method='PATCH', renderer="gtw")
def update_ticket(request):
    """
    Update a ticket
    """
    ticket = request.db.query(models.Ticket).get(request.matchdict['id'])
    if ticket:
        ticket.is_open = request.PATCH['is_open']
        if request.PATCH.get('message', None):
            ticket.comments.append(models.Comment(author=request.PATCH['comment_author'], message=request.PATCH['message']))
        try:
            request.db.commit()
            return HTTPAccepted()
        except:
            request.db.rollback()
            raise
    else:
        return HTTPNotFound()


if __name__ == '__main__':

    def bind_db(event):
        event.request.db = event.request.registry.Session()

    #Database configurator
    config = utils.Configuration.from_env()
    engine = models.create_engine_from_config(config)

    config_pyrmd = Configurator(settings=dict(config.items()))
    config_pyrmd.add_route('index', '/')

    config_pyrmd.add_route('ArticlePkg',
        '/api/%s/packages/{id}/' % config.get('http_server', 'version'))
    config_pyrmd.add_route('Attempt',
        '/api/%s/attempts/{id}/' % config.get('http_server', 'version'))
    config_pyrmd.add_route('Ticket',
        '/api/%s/tickets/{id}/' % config.get('http_server', 'version'))
    config_pyrmd.add_route('new_ticket',
        '/api/%s/tickets/' % config.get('http_server', 'version'))
    config_pyrmd.add_route('update_ticket',
        '/api/%s/tickets/{id}/' % config.get('http_server', 'version'))
    config_pyrmd.add_route('list_package',
        '/api/%s/packages/' % config.get('http_server', 'version'))
    config_pyrmd.add_route('list_ticket',
        '/api/%s/tickets/' % config.get('http_server', 'version'))
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
