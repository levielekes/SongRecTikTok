from enum import IntEnum


class StatusFetchShazam(IntEnum):
    NOT_FETCHED = 0
    IN_PROGRESS = 1
    DOWNLOADED = 2
    PROCESSED = 3
    BLOCKED_KEYWORDS = 4
