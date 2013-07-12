# coding: utf-8
import sys

import scieloapi
import plumber

import utils
import notifier


STATUS_OK = 'ok'
STATUS_WARNING = 'warning'
STATUS_ERROR = 'error'

#config = utils.Configuration.from_env()


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


class PISSNValidationPipe(ValidationPipe):
    """
    Verify if PISSN exists on SciELO Manager and if it's valid.

    The analyzed atribute is ``.//issn[@pub-type="ppub"]``
    """
    _stage_ = 'issn'

    def validate(self, package_analyzer):

        data = package_analyzer.xml

        journal_pissn = data.findtext(".//issn[@pub-type='ppub']")

        if utils.is_valid_issn(journal_pissn):
            return [STATUS_OK, '']
        else:
            return [STATUS_ERROR, 'print ISSN is invalid']


class EISSNValidationPipe(ValidationPipe):
    """
    Verify if EISSN exists on SciELO Manager and if it's valid.

    The analyzed atribute is ``.//issn/@pub-type="epub"``
    """
    _stage_ = 'issn'

    def validate(self, package_analyzer):

        data = package_analyzer.xml

        eissn = data.findtext(".//issn[@pub-type='epub']")

        if utils.is_valid_issn(eissn):
            #Validate journal_eissn against SciELO scieloapi.Manager
            return [STATUS_OK, '']
        else:
            return [STATUS_ERROR, 'electronic ISSN is invalid']


if __name__ == '__main__':
    messages = utils.recv_messages(sys.stdin, utils.make_digest)
    ppl = plumber.Pipeline(PISSNValidationPipe,
                           EISSNValidationPipe)

    try:
        results = [msg for msg in ppl.run(messages)]
    except KeyboardInterrupt:
        sys.exit(0)
