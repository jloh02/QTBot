import datetime


def compute_next_deadline(frequency: str) -> datetime.date:
    now = datetime.datetime.now()
    days = int(frequency.replace("d", ""))
    return now + datetime.timedelta(days=days) + datetime.timedelta(hours=12)
