import os
import json
import datetime
from config import config

group_data_cache = {}


def get_group_data_path():
    return f"{config.get('BASE_PATH')}/group_data.json"


def read_group_data():
    global group_data_cache
    if not os.path.isfile(get_group_data_path()):
        return
    group_data_cache.clear()
    with open(get_group_data_path(), "r") as f:
        group_data_cache.update(json.load(f))


def write_group_data():
    global group_data_cache
    dir = os.path.dirname(get_group_data_path())
    if not os.path.isdir(dir):
        os.makedirs(dir)
    with open(get_group_data_path(), "w") as f:
        json.dump(group_data_cache, f)


def register_group(chat_id: int, frequency: str):
    group_data_cache[str(chat_id)] = {
        "frequency": frequency,
        "last_completed": {},
        "streaks": {},
    }
    write_group_data()


def mark_done(chat_id: int, user: str):
    group = group_data_cache.get(str(chat_id), None)
    if group is None:
        return
    today = datetime.date.today().isoformat()
    last_done = group["last_completed"].get(user)
    if last_done != today:
        group["last_completed"][user] = today
        group["streaks"][user] = group["streaks"].get(user, 0) + 1
        write_group_data()


def get_group_summary(chat_id: int) -> tuple[dict, dict]:
    group = group_data_cache.get(str(chat_id), {})
    return group.get("streaks", {}), group.get("last_completed", {})


def get_all_groups():
    return group_data_cache.items()
