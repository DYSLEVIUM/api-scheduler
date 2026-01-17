from enum import Enum


class ScheduleType(str, Enum):
    INTERVAL = "interval"
    WINDOW = "window"
