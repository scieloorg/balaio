#coding: utf-8
import time
import logging
import argparse
from datetime import datetime
from StringIO import StringIO

import transaction
import scieloapi

from lib import utils, models, meta_extractor, package
from lib.uploader import StaticScieloBackend

FILES_EXTENSION = ['xml', 'pdf',]
IMAGES_EXTENSION = ['tif', 'eps']
NAME_ZIP_FILE = 'images.zip'
STATIC_PATH = 'articles'

logger = logging.getLogger('checkout')

def upload_static_files(package_analyzer, conn_static):
    """
    Send the ``PDF``, ``XML`` files to the static server

    :param package_analyzer: PackageAnalyzer object
    :param conn_static: connection with static server
    """
    uri_dict = {}
    filename_list = []

    with conn_static as static:

        for ext in FILES_EXTENSION:
            for static_file in package_analyzer.get_fps(ext):
                uri = static.send(StringIO(static_file.read()),
                                  utils.get_static_path(STATIC_PATH,
                                                        'tmp',
                                                        static_file.name))
                uri_dict[ext] = uri

        for ext in IMAGES_EXTENSION:
            filename_list += package_analyzer.get_ext(ext)

        subzip_img = package_analyzer.subzip(*filename_list)

        static_path = utils.get_static_path(STATIC_PATH,
                                            'tmp', NAME_ZIP_FILE)

        uri = static.send(subzip_img, static_path)

        uri_dict['img'] = uri

        return uri_dict


def upload_meta_front(package_analyzer, client, uri_dict):
    """
    Send the extracted front to SciELO Manager

    :param package_analyzer: PackageAnalyzer object
    :param client: Manager client connection
    :param uri_dict: dict content the uri to the static file
    """
    dict_filter = {}

    ppl =  meta_extractor.get_meta_ppl()

    xml = package_analyzer.xml

    meta = package_analyzer.meta

    dict_filter['pissn'] = meta['journal_pissn']
    dict_filter['eissn'] = meta['journal_eissn']
    dict_filter['volume'] = meta['issue_volume']
    dict_filter['number'] = meta['issue_number']
    dict_filter['suppl_number'] = meta['issue_suppl_number']
    dict_filter['suppl_volume'] = meta['issue_suppl_volume']
    dict_filter['publication_year'] = meta['issue_year']

    issue = next(client.issues.filter(**dict_filter))

    data = {
        'issue': issue['resource_uri'],
        'front': next(ppl.run(xml, rewrap=True)),
        'xml_url': uri_dict['xml'],
        'pdf_url': uri_dict['pdf'],
        'images_url': uri_dict['img'],
    }

    client.articles.post(data)


def checkout_procedure_by_attempt(item):
    """
    This function performs some operations related to checkout attempts
        - Upload static files to the backend
        - Upload the front metadata to the Manager
        - Set queued_checkout = False

    :param item: item (attempt, client, conn)
    """
    try:
        attempt, client, conn = item

        logger.info("Starting checkout to attempt: %s" % attempt)

        attempt.checkout_started_at = datetime.now()

        logger.info("Set checkout_started_at to: %s" % attempt.checkout_started_at)

        uri_dict = upload_static_files(attempt.analyzer, conn)

        logger.info("Upload static files for attempt: %s" % attempt)

        upload_meta_front(attempt.analyzer, client, uri_dict)

        logger.info("Set queued_checkout to False attempt: %s" % attempt)

        attempt.queued_checkout = False
    except Exception as e:
        logger.critical("some exception occurred while processing the package %s, traceback: %s" % (attempt.analyzer._filename, e.message))


def checkout_procedure_by_package(item):
    """
    This function performs some operations related to packages
        - Upload static files to the backend
        - Upload the front metadata to the Manager

    :param item: item (package, client, conn)
    """
    try:
        pkg, client, conn = item

        logger.info("Starting checkout to package: %s" % pkg._filename)

        uri_dict = upload_static_files(pkg, conn)

        logger.info("Upload static files for package: %s" % pkg._filename)

        upload_meta_front(pkg, client, uri_dict)

        logger.info("Upload meta front for package: %s" % pkg._filename)
    except Exception as e:
        logger.critical("some exception occurred while processing the package %s, traceback: %s" % (pkg._filename, e.message))


def main(config):

    parser = argparse.ArgumentParser(description='Checkout SPS packages from command line\
                                    and checkout attempts like deamon process.')

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-d', '--directory',
                        dest='directory',
                        help='indicate the path direcotry to process')

    group.add_argument('-f', '--file',
                        dest='file',
                        help='indicate the path of package ``.zip` to process')

    group.add_argument('-a', '--attempts',
                        action='store_true',
                        help='processes attempts considering the proceed_to_checkout\
                        = True and checkout_started_at = None')

    parser.add_argument('-v', '--version',
                        action='version',
                        version='%(prog)s 0.1')

    args = parser.parse_args()

    session = models.Session()

    client = scieloapi.Client(config.get('manager', 'api_username'),
                              config.get('manager', 'api_key'),
                              config.get('manager', 'api_url'), 'v1')

    conn = StaticScieloBackend(config.get('static_server', 'username'),
                               config.get('static_server', 'password'),
                               config.get('static_server', 'path'),
                               config.get('static_server', 'host'))

    if args.attempts:

        while True:

            attempts_checkout = session.query(models.Attempt).filter_by(
                                              proceed_to_checkout=True,
                                              checkout_started_at=None).all()

            if attempts_checkout:
                try:
                    for attempt in attempts_checkout:
                        attempt.queued_checkout=True
                        checkout_procedure_by_attempt((attempt, client, conn))

                    transaction.commit()
                except:
                    transaction.abort()
                    raise

            time.sleep(config.getint('checkout', 'mins_to_wait') * 60)

    if args.directory:
        packages = [package.PackageAnalyzer(fp) for fp in utils.get_zip_files(args.directory)]
        for pkg in packages:
            checkout_procedure_by_package((pkg, client, conn))

    if args.file:
        pkg = package.PackageAnalyzer(args.file)
        checkout_procedure_by_package((pkg, client, conn))


if __name__ == '__main__':
    config = utils.balaio_config_from_env()

    utils.setup_logging(config)

    models.Session.configure(bind=models.create_engine_from_config(config))

    print('Start checkout process...')

    main(config)
