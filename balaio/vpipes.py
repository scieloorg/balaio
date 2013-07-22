import plumber

import scieloapitoolbelt


Pipe = plumber.Pipe


class Pipeline(plumber.Pipeline):

    def configure(self, scieloapi, notifier):
        """
        Allow you to pass keyword arguments to all
        pipes before running the pipeline.
        """
        new_pipes = []

        for pipe in self._pipes:
            def config_wrap(data):
                return pipe(data, scieloapi=scieloapi, notifier_dep=notifier)
            new_pipes.append(config_wrap)

        self._pipes = new_pipes


class ValidationPipe(plumber.Pipe):
    """
    Specialized Pipe which validates the data and notifies the result.
    """
    def __init__(self,
                 data,
                 scieloapi=None,
                 notifier_dep=None,
                 scieloapitools_dep=scieloapitoolbelt):
        """
        `data` is an iterable that will pass thru the pipe.
        `scieloapi` is an instance of scieloapi.Client.
        """
        super(ValidationPipe, self).__init__(data)

        if not notifier_dep:
            raise ValueError('missing argument notifier')
        if not scieloapi:
            raise ValueError('missing argument scieloapi')

        self._notifier = notifier_dep
        self._scieloapi = scieloapi
        self._sapi_tools = scieloapitools_dep

    def transform(self, item):
        """
        Performs a transformation to one `item` of data iterator.

        `item` is a pair comprised of instances of models.Attempt
        and checkin.PackageAnalyzer.
        """
        attempt, package_analyzer, journal = item
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

