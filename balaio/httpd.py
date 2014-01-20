import sys
import argparse

import transaction
from wsgiref.simple_server import make_server

from pyramid.response import Response
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound, HTTPAccepted, HTTPCreated
from pyramid.view import notfound_view_config, view_config
from pyramid.events import NewRequest

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

import utils
import models
import health


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
    return Response("Balaio's HTTP server.")


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
            'filters': filters,
            'total': request.db.query(func.count(models.ArticlePkg.id)).filter_by(**filters).scalar(),
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
            'filters': filters,
            'total': request.db.query(func.count(models.Attempt.id)).filter_by(**filters).scalar(),
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


@view_config(route_name='ticket', request_method='GET', renderer="gtw")
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
            'filters': filters,
            'total': request.db.query(func.count(models.Ticket.id)).filter_by(**filters).scalar(),
            'objects': [ticket.to_dict() for ticket in tickets]}


@view_config(route_name='ticket', request_method='POST', renderer="gtw")
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
        transaction.commit()
    except:
        request.db.rollback()
        raise

    return HTTPCreated()


@view_config(route_name='Ticket', request_method='POST', renderer="gtw")
def update_ticket(request):
    """
    Update a ticket
    """
    ticket = request.db.query(models.Ticket).get(request.matchdict['id'])
    if ticket:
        ticket.is_open = request.POST['is_open']
        if request.POST.get('message', None):
            ticket.comments.append(models.Comment(author=request.POST['comment_author'], message=request.POST['message']))
        try:
            transaction.commit()
            return HTTPAccepted()
        except:
            request.db.rollback()
            raise
    else:
        return HTTPNotFound()


@view_config(route_name='status', request_method='GET', renderer='json')
def health_status(request):
    """
    Display the health status of the system.
    """
    health_status = request.registry.health_status
    report = health_status.latest_report
    items = {k.__class__.__name__: v for k, v in report.items()}

    return {'meta': {'last_refresh': health_status.since()},
            'results': items}


def main(config, engine):
    """
    Returns a pyramid app.

    :param config: an instance of :class:`utils.Configuration`.
    :param engine: sqlalchemy engine.
    """
    def bind_db(event):
        event.request.db = event.request.registry.Session()

    def update_health_status(event):
        event.request.registry.health_status.update()


    config_pyrmd = Configurator(settings=dict(config.items()))
    config_pyrmd.add_route('index', '/')
    config_pyrmd.add_route('status', '/status/')

    # get
    config_pyrmd.add_route('ArticlePkg', '/api/v1/packages/{id}/')
    config_pyrmd.add_route('Attempt', '/api/v1/attempts/{id}/')
    config_pyrmd.add_route('Ticket', '/api/v1/tickets/{id}/')

    # lists
    config_pyrmd.add_route('list_package', '/api/v1/packages/')
    config_pyrmd.add_route('list_attempts', '/api/v1/attempts/')

    # tickets new and update
    config_pyrmd.add_route('ticket', '/api/v1/tickets/')

    config_pyrmd.add_renderer('gtw', factory='renderers.GtwFactory')

    #DB session bound to each request
    config_pyrmd.registry.Session = models.ScopedSession
    config_pyrmd.registry.Session.configure(bind=engine)
    config_pyrmd.add_subscriber(bind_db, NewRequest)

    # Health check is available globally on the application
    # at `request.registry.health_check` and is updated
    # periodically.
    check_list = health.CheckList(refresh=1)
    check_list.add_check(health.DBConnection(engine))

    config_pyrmd.registry.health_status = check_list
    config_pyrmd.add_subscriber(update_health_status, NewRequest)

    config_pyrmd.scan('httpd')

    return config_pyrmd.make_wsgi_app()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=u'HTTP Server')
    parser.add_argument('-c',
                        action='store',
                        dest='configfile',
                        required=True)

    args = parser.parse_args()

    # app setup
    config = utils.Configuration.from_file(args.configfile)
    engine = models.create_engine_from_config(config)
    app = main(config, engine)

    listening = config.get('http_server', 'ip')
    port = config.getint('http_server', 'port')

    server = make_server(listening, port, app)

    print "HTTP Server started listening %s on port %s" % (listening, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit('HTTP server stopped.')

