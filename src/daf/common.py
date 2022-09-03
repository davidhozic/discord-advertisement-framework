"""
    This module contains all the different constants that
    can be common to more modules
"""
from enum import Enum

# TIME CONSTANTS
C_DAY_TO_SECOND = 86400
C_HOUR_TO_SECOND = 3600
C_MINUTE_TO_SECOND = 60

# TASK CONSTANTS
C_TASK_SLEEP_DELAY = 0.010 # Advertiser task sleep

# RATE LIMIT CONSTANTS
RLIM_USER_WAIT_TIME = 1.5  # Initial rate limit avoidance time for user accounts
RLIM_SAFETY_FACTOR = 1.10  # In case of a rate limit, wait times this more

# SQL CONFIGURATION
SQL_MAX_SAVE_ATTEMPTS = 10
SQL_MAX_EHANDLE_ATTEMPTS = 3
SQL_RECOVERY_TIME = 0.5
SQL_RECONNECT_TIME = 5 * C_MINUTE_TO_SECOND
SQL_RECONNECT_ATTEMPTS = 3
SQL_CONNECTOR_TIMEOUT = 6

# OTHER CONSTANTS
C_FILE_NAME_FORBIDDEN_CHAR = ('<','>','"','/','\\','|','?','*',":")

# MESSAGE SETTINGS
C_VC_CONNECT_TIMEOUT = 3 # Timeout of voice channels
C_PERIOD_MINIMUM_SEC = 1 # Minimal seconds the period can be


# Classes
class AdvertiseTaskType(Enum):
    """
    Used for identifying advertiser tasks
    """
    TEXT_ISH = 0
    VOICE = 1