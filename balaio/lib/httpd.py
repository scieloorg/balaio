import logging
import xmlrpclib

import transaction

from pyramid.response import Response
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.view import notfound_view_config, view_config
from pyramid.events import NewRequest
from pyramid.settings import asbool
from pyramid_xmlrpc import XMLRPCView

from sqlalchemy import func
from sqlalchemy.exc import DataError

from . import models, health


logger = logging.getLogger(__name__)


def get_query_filters(model, request_params):
    filters = {}
    for name, value in request_params.items():
        if hasattr(model, name):
            filters[name] = value
    return filters


# ------------------------------
# View-functions
# ------------------------------
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


@view_config(route_name='list_attempt_members', request_method='GET', renderer='json')
def list_files_from_attempt(request):
    """
    List all files bound to an Attempt.
    """
    attempt_id = request.matchdict.get('attempt_id', None)
    try:
        attempt = request.db.query(models.Attempt).get(attempt_id)
    except DataError:
        return HTTPNotFound()

    if attempt is None:
        return HTTPNotFound()

    return attempt.analyzer.get_classified_members()


@view_config(route_name='get_attempt_member', request_method='GET', renderer='json')
def get_file_from_attempt(request):
    """Get a portion of a package bound to an Attempt.

    Get a specific member, by name (raw):
    `/api/:api_id/files/:attempt_id/:target?file=:member&raw=true`

    .. note::
      The attributes `raw` and `full` are mutually exclusives, and will
      raise an HTTPBadRequest if used together.


    Get a specific member, by name:
    `/api/:api_id/files/:attempt_id/:target.zip?file=:member`

    Get more than one specific members, by name:
    `/api/:api_id/files/:attempt_id/:target.zip?file=:member&file=:member2`

    Get the full package:
    `/api/:api_id/files/:attempt_id/:target.zip?full=true`
    """
    has_body = False

    attempt_id = request.matchdict.get('attempt_id', None)
    target = request.matchdict.get('target', None)

    try:
        attempt = request.db.query(models.Attempt).get(attempt_id)
    except DataError:
        return HTTPNotFound()

    if attempt is None:
        return HTTPNotFound()

    is_full = asbool(request.GET.get('full', False))
    is_raw = asbool(request.GET.get('raw', False))

    if is_full and is_raw:
        return HTTPBadRequest()

    response = Response(status_code=200)

    # Get the full package.
    if is_full:
        response.content_type = 'application/zip'
        response.app_iter = open(attempt.filepath, 'rb')
        has_body = True

    elif is_raw:
        member_name = request.GET.get('file')
        response.content_type = 'text/xml'
        response.app_iter = attempt.analyzer.get_fp(member_name)
        has_body = True

    else:
        response.content_type = 'application/zip'

        # Get partial portions of the package.
        files = [member for attr, member in request.GET.items() if attr == 'file']

        try:
            if files:
                response.app_iter = attempt.analyzer.subzip(*files)
                has_body = True
        except ValueError:
            return HTTPBadRequest()

    return response if has_body else HTTPBadRequest()


# ------------------------------
# XML-RPC Endpoint
# ------------------------------
@view_config(route_name='rpc')
class XMLRPCEndpoint(XMLRPCView):
    """XML-RPC Server.

    The server listens the endpoint `/api/v1/_rpc/`.

    Fault codes and descriptions:
      - `ServerError`: An unhandled exception occured
      - `ValueError`: Argument with invalid value
      - `TypeError`: Argument of an invalid type
    """

    def status(self):
        """Check if the XML-RPC endpoint is listening.
        """
        return True

    def proceed_to_checkout(self, attempt_id):
        """Set an attempt as being ready for checkout.
        """
        attempt = self.request.db.query(models.Attempt).get(attempt_id)
        if not attempt:
            return xmlrpclib.Fault('ValueError', 'Unknown attempt with id %s.' % attempt_id)

        if attempt.is_expired:
            return xmlrpclib.Fault('ValueError', 'Attempt %s is expired.' % attempt_id)

        attempt.proceed_to_checkout = True
        try:
            transaction.commit()

        except Exception as e:
            logger.error(e)
            transaction.abort()
            return xmlrpclib.Fault('ServerError', 'An unexpected error occurred.')

        return True

    def expire_attempt(self, attempt_id):
        """Mark an attempt as expired.

        Expired attempts are not eligible to the checkout process and
        their related zip packages are deleted.

        It is not possible to expire attempts with
        `proceed_to_checkout == True`.

        .. note::
          Since this function is idempotent, it can be called many times without
          undesired side-effects.
        """
        attempt = self.request.db.query(models.Attempt).get(attempt_id)
        if not attempt:
            return xmlrpclib.Fault('ValueError', 'Unknown attempt with id %s.' % attempt_id)

        try:
            attempt.expire()

        except IOError as e:
            logger.error(e)
            return xmlrpclib.Fault('ServerError', 'An unexpected error occurred.')

        except ValueError as e:
            logger.error(e)
            return xmlrpclib.Fault('ValueError', e.message)

        else:
            try:
                transaction.commit()

            except Exception as e:
                logger.error(e)
                transaction.abort()
                return xmlrpclib.Fault('ServerError', 'An unexpected error occurred.')

        return True



# ------------------------------
# Webapp entry point
# ------------------------------
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

    # lists
    config_pyrmd.add_route('list_package', '/api/v1/packages/')
    config_pyrmd.add_route('list_attempts', '/api/v1/attempts/')

    # XML-RPC
    config_pyrmd.add_route('rpc', '/api/v1/_rpc/')

    # files
    config_pyrmd.add_route('list_attempt_members', '/api/v1/files/{attempt_id}/')
    config_pyrmd.add_route('get_attempt_member', '/api/v1/files/{attempt_id}/{target}')

    config_pyrmd.add_renderer('gtw', factory='.renderers.GtwFactory')

    #DB session bound to each request
    config_pyrmd.registry.Session = models.ScopedSession
    config_pyrmd.registry.Session.configure(bind=engine)
    config_pyrmd.add_subscriber(bind_db, NewRequest)

    # Health check is available globally on the application
    # at `request.registry.health_check` and is updated
    # periodically.
    check_list = health.CheckList(refresh=1)
    check_list.add_check(health.DBConnection(engine))
    check_list.add_check(health.NotificationsOption(config))
    check_list.add_check(health.Monitor())
    check_list.add_check(health.Validator())

    config_pyrmd.registry.health_status = check_list
    config_pyrmd.add_subscriber(update_health_status, NewRequest)

    config_pyrmd.scan(package='.httpd')

    return config_pyrmd.make_wsgi_app()

