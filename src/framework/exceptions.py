
class DAFError(Exception):
    """~ class ~
    @Info: Base exception class for all DAF exceptions."""
    pass


class DAFInitError(DAFError):
    """~ class ~
    @Info: Raised for initialization errors."""
    pass


class DAFAlreadyAddedError(DAFError):
    """~ class ~
    @Info: Raised when an object is added to the framework but already exists."""
    pass


class DAFParameterError(DAFError):
    """~ class ~
    @Info: Raised when theres an parameter exception."""
    pass

class DAFMissingParameterError(DAFParameterError):
    """~ class ~
    @Info: Raised when a parameter is missing."""
    pass

class DAFInvalidParameterError(DAFParameterError):
    """~ class ~
    @Info: Raised when a parameter is invalid."""
    pass


class DAFNotFoundError(DAFError):
    """~ class ~
    @Info: Raised when an object is not found."""
    pass