# coding: utf-8
import scieloapi
import plumber

import utils
import notifier

#config = utils.Configuration.from_env()

STATUS_OK = 'ok'
STATUS_WARNING = 'warning'
STATUS_ERROR = 'error'

#scieloapi_client = scieloapi.Client(config.get('manager', 'api_username'),
#                                    config.get('manager', 'api_key')
scieloapi_client = scieloapi.Client('gustavo.fonseca',
                                    'ef7329151f5d5352f4b7bb0000deff0123865138')

class ValidationPipe(plumber.Pipe):
    """
    Specialized Pipe which validates the data and notifies the result
    """
    def __init__(self, data, scieloapi=None, notifier_dep=notifier.Notifier):
        """
        `scieloapi` is an instance of scieloapi.Client
        """
        super(ValidationPipe, self).__init__(data)
        self._notifier = notifier_dep()

        if scieloapi:
            self._scieloapi = scieloapi
        else:
            raise ValueError('missing argument scieloapi')

    def transform(self, data):
        # data = (Attempt, PackageAnalyzer)
        # PackagerAnalyzer.xml
        attempt, package_analyzer = data
        result_status, result_description = self.validate(package_analyzer)

        message = {
            'stage': self._stage_,
            'status': result_status,
            'description': result_description,
        }

        self._notifier.validation_event(message)

        return data

