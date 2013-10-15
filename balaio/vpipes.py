import logging

from plumber import Pipe, Pipeline

import scieloapitoolbelt


logger = logging.getLogger(__name__)


class ValidationPipe(Pipe):

    """
    Specialized Pipe which validates the data and notifies the result.
    """
    def __init__(self, notifier, scieloapi, sapi_tools):
        self._notifier = notifier
        self._scieloapi = scieloapi
        self._sapi_tools = sapi_tools

    def transform(self, item):
        """
        Performs a transformation to one `item` of data iterator.

        `item` is a tuple comprised of instances of models.Attempt, a
        checkin.PackageAnalyzer, a dict of journal and issue data.
        """
        logger.debug('%s started processing %s' % (self.__class__.__name__, item[0]))

        result_status, result_description = self.validate(item)

        self._notifier(item[0]).tell(result_description, result_status, label=self._stage_)

        return item

    def validate(self, item):
        """
        Performs the validation of `item`.

        `item` is a tuple comprised of instances of models.Attempt, a
        checkin.PackageAnalyzer, a dict of journal and issue data.
        """
        raise NotImplementedError()

