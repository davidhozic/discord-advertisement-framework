"""
    ~ const ~
    This module contains all the different constants that
    can be common to more modules
"""
C_DAY_TO_SECOND = 86400
C_HOUR_TO_SECOND= 3600
C_MINUTE_TO_SECOND = 60

C_TASK_SLEEP_DELAY   = 0.010  # Advertiser task sleep
C_VC_CONNECT_TIMEOUT = 3    # Timeout of voice channels


C_RATE_LIMIT_INITIAL_USERS = 1    # Initial rate limit avoidance time for user accounts (0 for bot accounts)
C_RATE_LIMIT_GROWTH_FACTOR = 1.25   # Factor with which to increment the ratelimit avoidance delay (when rate limit get's hit)
C_RATE_LIMIT_SAFETY_FACTOR = 2    # In case of a rate limit, wait times this more

C_FILE_NAME_FORBIDDEN_CHAR = ('<','>','"','/','\\','|','?','*',":")
