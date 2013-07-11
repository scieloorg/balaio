# coding: utf-8
import scieloapi
import plumber

import utils
import notifier

#config = utils.Configuration.from_env()

STATUS_OK = 'ok'
STATUS_WARNING = 'warning'
STATUS_ERROR = 'error'


class ValidationPipe(plumber.Pipe):
    """
    Specialized Pipe which validates the data and notifies the result.
    """
    def __init__(self, data, scieloapi=None, notifier_dep=notifier.Notifier):
        """
        `data` is an iterable that will pass thru the pipe.
        `scieloapi` is an instance of scieloapi.Client.
        """
        super(ValidationPipe, self).__init__(data)

        self._notifier = notifier_dep()
        if scieloapi:
            self._scieloapi = scieloapi
        else:
            raise ValueError('missing argument scieloapi')

    def transform(self, item):
        """
        Performs a transformation to one `item` of data iterator.

        `item` is a pair comprised of instances of models.Attempt
        and checkin.PackageAnalyzer.
        """
        attempt, package_analyzer = item
        result_status, result_description = self.validate(package_analyzer)

        message = {
            'stage': self._stage_,
            'status': result_status,
            'description': result_description,
        }

        self._notifier.validation_event(message)

        return item

    def validate(self, package):
        """
        Performs the validation of `package`.

        `package` is a checkin.PackageAnalyzer instance,
        representing the article package under validation.
        """
        raise NotImplementedError()

