"""
Contains the definitions related to errors that can be raised inside the daf.
"""

class DAFError(Exception):
    """
    Base exception class for all DAF exceptions.

    Parameters
    -------------
    message: str
        The exception message.
    code: int
        The error code.
    """
    def __init__(self, message: str, code: int):
        self.code = code # Error code
        super().__init__(message)


class DAFNotFoundError(DAFError):
    """
    Raised when an object is not found.

    Parameters
    -------------
    message: str
        The exception message.
    code: int
        The error code.
    """


class DAFSQLError(DAFError):
    """
    Raised whenever there's an error with SQL.

    Parameters
    -------------
    message: str
        The exception message.
    code: int
        The error code.
    """

# Error Codes
# Guild codes
DAF_SNOWFLAKE_NOT_FOUND = 1          #: Guild with specified snowflake was not found (or user).
DAF_USER_CREATE_DM = 2               #: Was unable to create DM with user (probably user not found).
# Data type codes
DAF_YOUTUBE_STREAM_ERROR = 3         #: The given youtube link could not be streamed (AUDIO, VoiceMESSAGE).
DAF_FILE_NOT_FOUND = 4               #: The given file was not found.
# SQL Exceptions
DAF_SQL_CREATE_TABLES_ERROR = 5      #: Unable to create all the tables.
DAF_SQL_LOOKUPTABLE_NOT_FOUND = 6    #: The lookup table was not found.
DAF_SQL_BEGIN_ENGINE_ERROR = 7       #: Unable to start engine.
DAF_SQL_CR_LT_VALUES_ERROR = 8       #: Unable to create lookuptables' rows.
DAF_SQL_CREATE_DT_ERROR = 9          #: Unable to create SQL data types.
DAF_SQL_CREATE_VPF_ERROR = 10        #: Unable to create views, procedures and functions.     
DAF_SQL_CURSOR_CONN_ERROR = 11       #: Unable to connect the cursor.
