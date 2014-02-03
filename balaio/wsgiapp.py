import sys
import argparse

from wsgiref.simple_server import make_server

import httpd, utils, models


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=u'HTTP Server')
    parser.add_argument('-c',
                        action='store',
                        dest='configfile',
                        required=False)

    args = parser.parse_args()

    # The user may specify a config file, or use the default
    # specified at `BALAIO_SETTINGS_FILE` env var.
    if args.configfile:
        config = utils.Configuration.from_file(args.configfile)
    else:
        config = utils.balaio_config_from_env()

    # Setting up SqlAlchemy engine.
    engine = models.create_engine_from_config(config)

    # Bootstrapping the app and the server.
    app = httpd.main(config, engine)
    listening = config.get('http_server', 'ip')
    port = config.getint('http_server', 'port')
    server = make_server(listening, port, app)

    print "HTTP Server started listening %s on port %s" % (listening, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit('HTTP server stopped.')
else:

    # Setting up the application entry point
    # to be used with Chaussette for example.

    config = utils.balaio_config_from_env()

    # Setting up SqlAlchemy engine.
    engine = models.create_engine_from_config(config)

    # Bootstrapping the app and the server.
    app = httpd.main(config, engine)

