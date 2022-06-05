"""
    ~ const ~
    This module contains all the different constants that
    can be common to more modules
"""
# TIME CONSTANTS
C_DAY_TO_SECOND = 86400
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60

# TASK CONSTANTS
C_TASK_SLEEP_DELAY   = 0.010  # Advertiser task sleep
C_VC_CONNECT_TIMEOUT = 3     # Timeout of voice channels

# RATE LIMIT CONSTANTS
C_USER_WAIT_TIME = 1.5               # Initial rate limit avoidance time for user accounts (0 for bot accounts)
C_RATE_LIMIT_SAFETY_FACTOR = 1.10    # In case of a rate limit, wait times this more

# SQL CONFIGURATION
C_FAIL_RETRIES = 10
C_RECOVERY_TIME = 0.25
C_RECONNECT_TIME = 5 * C_MINUTE_TO_SECOND
C_RECONNECT_ATTEMPTS = 3 
C_CONNECTOR_TIMEOUT = 3

# OTHER CONSTANTS
C_FILE_NAME_FORBIDDEN_CHAR = ('<','>','"','/','\\','|','?','*',":")

