#coding: utf-8
import time
import argparse
import transaction

import models
import utils


class CheckoutList(list):
    """
    Child class adapted to have a scpecific behavior in append method.
    """

    def __init__(self, *args, **kwgars):
        """
        :param session: session passed as param to the object
        """
        super(CheckoutList, self).__init__()
        self.session = kwgars.get('session')

    def append(self, item):
        """
        Add the param item on a parent list if is a expected type

        :param item: Any Attempt like object
        """
        if not isinstance(item, models.Attempt):
            raise TypeError, 'item is not a Attempt type'

        session.query(models.Attempt).filter_by(id=item.id).update(
                                                    {'queued_checkout': True})
        transaction.commit()

        super(CheckoutList, self).append(item)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=u'Checkout')
    parser.add_argument('-c',
                        action='store',
                        dest='configfile',
                        required=True)

    args = parser.parse_args()

    config = utils.Configuration.from_env()

    Session = models.Session
    Session.configure(bind=models.create_engine_from_config(config))
    session = Session()

    while True:

        attempts_checkout = session.query(models.Attempt).filter_by(
                                          proceed_to_checkout=True).all()

        #Process only if exists itens
        if attempts_checkout:

            checkout_lst = CheckoutList(session=Session)

            for attempt in attempts_checkout:
                checkout_lst.append(attempt)

        time.sleep(config.getint('checkout', 'time') * 60)
