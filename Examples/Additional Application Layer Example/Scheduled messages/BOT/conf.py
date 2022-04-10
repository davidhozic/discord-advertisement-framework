"""
    ~  Configuration  ~

@Info:
    This file contains everything you need
    to configure to send scheduled messages.
"""

# USER ACCOUNT TOKEN FOR THE BOT
TOKEN = ""


# TIME SETTINGS
MIN_TO_SEC = 60
HOUR_TO_SEC = 60 * MIN_TO_SEC
DAY_TO_SEC = 24 * HOUR_TO_SEC

# TIMING
CHECK_PERIOD  = 20  # Period in second at which to check the files
DELETE_PERIOD = 14 * DAY_TO_SEC # Period after which sent messages will be deleted

# FOLDERS
UPLOAD_FOLDER = "./OBV/UPLOAD_FILES_HERE"           # Folder to which to upload json scheduled messages to
UPLOAD_ATTEMPT_FOLDER = "./OBV/LOGS_OF_ATTEMPTS"    # Folder to which to send logs
UPLOAD_TEMP_FILE_FOLDER = "./TMP"   # Folder for creating temporary files

# AUTHORIZED GUILDS and CHANNELS
## You need to define the guilds and channels to which you want to send here, otherwise the scheduled message will be ignored.
WHITELISTED_GUILDS = [
    {"SERVER-ID" : 12345, "CHANNEL-IDs" : [6789, 10111213]}
]

# Channel ID's protected from having messages deleted
DO_NOT_DELETE_CH_IDS =  [
                            12345,
                            6789,
                            10120
                        ]
