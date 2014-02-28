#coding: utf-8
import time
import logging
from datetime import datetime
from StringIO import StringIO
from multiprocessing.dummy import Pool as ThreadPool

import transaction
import scieloapi

import utils
import models
import meta_extractor
from uploader import StaticScieloBackend


FILES_EXTENSION = ['xml', 'pdf',]
IMAGES_EXTENSION = ['tif', 'eps']
NAME_ZIP_FILE = 'images.zip'
STATIC_PATH = 'articles'

logger = logging.getLogger(__name__)


class CheckoutList(list):
    """
    Child class of list adapted to evaluate the type of the object when use the
    method append, if it's a models.Attempt change the boolean value of the
    attribute queued_checkout.
    """

    def append(self, item):
        """
        Add the param item on a parent list if is a expected type

        :param item: Any Attempt like object
        """
        if isinstance(item, models.Attempt):
            item.queued_checkout=True

        super(CheckoutList, self).append(item)


def upload_static_files(attempt, conn_static):
    """
    Send the ``PDF``, ``XML`` files to the static server

    :param attempt: Attempt object
    :param conn_static: connection with static server
    """
    uri_dict = {}
    filename_list = []

    with conn_static as static:

        for ext in FILES_EXTENSION:
            for static_file in attempt.analyzer.get_fps(ext):
                uri = static.send(StringIO(static_file.read()),
                                  utils.get_static_path(STATIC_PATH,
                                                        attempt.articlepkg.aid,
                                                        static_file.name))
                uri_dict[ext] = uri

        for ext in IMAGES_EXTENSION:
            filename_list += attempt.analyzer.get_ext(ext)

        subzip_img = attempt.analyzer.subzip(*filename_list)

        static_path = utils.get_static_path(STATIC_PATH,
                                            attempt.articlepkg.aid, NAME_ZIP_FILE)

        uri = static.send(subzip_img, static_path)

        uri_dict['img'] = uri

        return uri_dict


def upload_meta_front(attempt, client, uri_dict):
    """
    Send the extracted front to SciELO Manager

    :param attempt: Attempt object
    :param cfg: cfguration file
    :param uri_dict: dict content the uri to the static file
    """
    dict_filter = {}

    ppl =  meta_extractor.get_meta_ppl()

    xml = attempt.analyzer.xml

    articlepkg = attempt.articlepkg

    dict_filter['pissn'] = articlepkg.journal_pissn if articlepkg.journal_pissn else None
    dict_filter['eissn'] = articlepkg.journal_eissn if articlepkg.journal_eissn else None
    dict_filter['volume'] = articlepkg.issue_volume if articlepkg.issue_volume else None
    dict_filter['number'] = articlepkg.issue_number if articlepkg.issue_number else None
    dict_filter['suppl_number'] = articlepkg.issue_suppl_number if articlepkg.issue_suppl_number else None
    dict_filter['suppl_volume'] = articlepkg.issue_suppl_volume if articlepkg.issue_suppl_volume else None
    dict_filter['publication_year'] = articlepkg.issue_year if articlepkg.issue_year else None

    issue = next(client.issues.filter(**dict_filter))

    data = {
        'issue': issue['resource_uri'],
        'front': next(ppl.run(xml, rewrap=True)),
        'xml_url': uri_dict['xml'],
        'pdf_url': uri_dict['pdf'],
        'images_url': uri_dict['img'],
    }

    client.articles.post(data)


def checkout_procedure(item):
    """
    This function performs some operations related to the checkout
        - Upload static files to the backend
        - Upload the front metadata to the Manager
        - Set queued_checkout = False

    :param attempt: item (Attempt, cfg)
    """
    attempt, client, conn = item

    logger.info("Starting checkout to attempt: %s" % attempt)

    attempt.checkout_started_at = datetime.now()

    logger.info("Set checkout_started_at to: %s" % attempt.checkout_started_at)

    uri_dict = upload_static_files(attempt, conn)

    logger.info("Upload static files for attempt: %s" % attempt)

    upload_meta_front(attempt, client, uri_dict)

    logger.info("Set queued_checkout to False attempt: %s" % attempt)

    attempt.queued_checkout = False


def main(config):

    session = models.Session()

    client = scieloapi.Client(config.get('manager', 'api_username'),
                              config.get('manager', 'api_key'),
                              config.get('manager', 'api_url'), 'v1')

    conn = StaticScieloBackend(config.get('static_server', 'username'),
                               config.get('static_server', 'password'),
                               config.get('static_server', 'path'),
                               config.get('static_server', 'host'))

    pool = ThreadPool()

    while True:

        attempts_checkout = session.query(models.Attempt).filter_by(
                                          proceed_to_checkout=True,
                                          checkout_started_at=None).all()

        #Process only if exists itens
        if attempts_checkout:

            checkout_lst = CheckoutList()

            try:
                for attempt in attempts_checkout:
                    checkout_lst.append((attempt, client, conn))

                #Execute the checkout procedure for each item
                pool.map(checkout_procedure, checkout_lst)

                transaction.commit()
            except:
                transaction.abort()
                raise

        time.sleep(config.getint('checkout', 'mins_to_wait') * 60)

    pool.close


if __name__ == '__main__':
    config = utils.balaio_config_from_env()
    utils.setup_logging(config)

    models.Session.configure(bind=models.create_engine_from_config(config))

    print('Start checkout process...')

    main(config)
