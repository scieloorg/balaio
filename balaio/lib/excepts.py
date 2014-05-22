class BalaioBaseError(Exception):
    """Base exception class.
    """


class DuplicatedPackage(BalaioBaseError):
    """Raised when a duplicated package is submitted to checkin.
    """


class InvalidXML(BalaioBaseError):
    """Raised when a package XML validation fail against the SPS XSD.
    """

class MissingXML(BalaioBaseError):
    """Raised when there is not a single XML inside a package.
    """

