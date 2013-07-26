import logging

import plumber

import scieloapitoolbelt


logger = logging.getLogger(__name__)
Pipe = plumber.Pipe


class Pipeline(plumber.Pipeline):

    def configure(self, **kwargs):
        """
        Allow you to pass keyword arguments to all
        pipes before running the pipeline.
        """
        new_pipes = []
        def make_wrapper(pipe):
            def config_wrap(data):
                logger.debug('Running config wrapper for %s with data %s' % (pipe, data))
                p = pipe(data)
                p.configure(**kwargs)
                return p
            return config_wrap

        for p in self._pipes:
            config_wrap = make_wrapper(p)
            logger.debug('%s as a wrapper to %s' % (config_wrap, p))
            new_pipes.append(config_wrap)

        self._pipes = new_pipes
        logger.debug('self._pipes are now %s' % self._pipes)

class ConfigMixin(object):
    """
    Allows a Pipe to be configurable.
    """
    def configure(self, **kwargs):
        requires = getattr(self, '__requires__', None)
        logger.debug('%s requires the dependencies: %s' % (self, ', '.join(requires)))

        if not requires:
            raise NotImplementedError('missing attribute __requires__')

        for attr_name, dep in [[k, v] for k, v in kwargs.items() if k in requires]:
            setattr(self, attr_name, dep)

        logger.debug('%s is now configured' % self)


class ValidationPipe(ConfigMixin, plumber.Pipe):
    """
    Specialized Pipe which validates the data and notifies the result.
    """
    __requires__ = ['_notifier', '_scieloapi', '_sapi_tools']

    def transform(self, item):
        """
        Performs a transformation to one `item` of data iterator.

        `item` is a pair comprised of instances of models.Attempt
        and checkin.PackageAnalyzer.
        """
        logger.debug('%s started processing %s' % (self.__class__.__name__, attempt))

        result_status, result_description = self.validate(item)

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

