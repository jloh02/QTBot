from enum import Enum

USER_DATA_KEY_BOT_MSG = "bot_msg"

FREQUENCY_OPTIONS = {"1d": "Once a day", "2d": "Once every 2 days", "7d": "Once a week"}


class ConvState(str, Enum):
    SelectFrequency = "SelectFrequency"


REMINDER_DEADLINE_IN_HOURS = 6
TIME_DEADLINE_LEEWAY_IN_HOURS = 12
