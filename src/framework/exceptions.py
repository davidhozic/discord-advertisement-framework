""" ~ exceptions ~
@Info: This module contains the definitons related to errors
       that can be raised inside the framework."""

# TODO: Documentation

class DAFError(Exception):
    """~ class ~
    @Info: Base exception class for all DAF exceptions."""
    def __init__(self, message: str, code: int):
        self.code = code # Error code
        super().__init__(message)


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


# Error Codes
## Guild codes
DAF_GUILD_ALREADY_ADDED         = 0 # Guild with specified snowflake is already added
DAF_GUILD_ID_REQUIRED           = 1 # Guild ID is required but was not passed    
DAF_GUILD_ID_NOT_FOUND          = 2 # Guild with specified snowflake was not found (or user)
DAF_USER_CREATE_DM              = 3
## Data type codes
DAF_INVALID_TYPE                = 4 # Object of invalid type was given
DAF_YOUTUBE_STREAM_ERROR        = 5 # The given youtube link could not be streamed (AUDIO, VoiceMESSAGE)
DAF_FILE_NOT_FOUND              = 6 # The given file was not found
## Missing error codes
DAF_MISSING_PARAMETER           = 7 # The parameter(s) is(are) missing
## Other
DAF_SQL_LOOKUPTABLE_NOT_FOUND   = 8 # The lookup table was not found