from enum import Enum

USER_DATA_KEY_BOT_MSG = "bot_msg"

FREQUENCY_OPTIONS = {"1d": "Once a day", "2d": "Once every 2 days", "7d": "Once a week"}


class ConvState(str, Enum):
    SelectFrequency = "SelectFrequency"


WELCOME_MESSAGE = (
    "Welcome to the QTDone Bot!\n\n"
    "Use /register to set up your group task reminder.\n"
    "Use /qtdone to log your task completion today.\n"
    "Stay consistent!"
)
