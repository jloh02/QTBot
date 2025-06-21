import os
import json
import utils
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


def register_user(chat_id: int, user: str, frequency: str):
    str_chat = str(chat_id)
    if str_chat not in group_data_cache:
        group_data_cache[str_chat] = {
            "frequencies": {},
            "next_deadline": {},
            "streaks": {},
        }
    group = group_data_cache[str_chat]
    group["frequencies"][user] = frequency
    group["next_deadline"][user] = utils.compute_next_deadline(frequency).isoformat()
    write_group_data()


def mark_done(chat_id: int, user: str, is_past_deadline: bool):
    str_chat = str(chat_id)
    group = group_data_cache.get(str_chat, None)
    if group is None:
        return
    freq = group["frequencies"].get(user)
    if freq:
        group["streaks"][user] = (
            1 if is_past_deadline else group["streaks"].get(user, 0) + 1
        )
        group["next_deadline"][user] = utils.compute_next_deadline(freq).isoformat()
    write_group_data()


def remove_user(chat_id: int, user: str):
    str_chat = str(chat_id)
    group = group_data_cache.get(str_chat, None)
    if group is None:
        return
    group["frequencies"].pop(user, None)
    group["next_deadline"].pop(user, None)
    group["streaks"].pop(user, None)
    write_group_data()


def get_user_frequency(chat_id: int, user: str) -> str | None:
    return get_group_frequencies(chat_id).get(user)


def get_user_next_deadline(chat_id: int, user: str) -> str | None:
    return get_group_next_deadline(chat_id).get(user)


def get_user_streak(chat_id: int, user: str) -> int | None:
    return get_group_streaks(chat_id).get(user)


def get_group_frequencies(chat_id: int) -> dict[str, str]:
    return group_data_cache.get(str(chat_id), {}).get("frequencies", {})


def get_group_next_deadline(chat_id: int) -> dict[str, str]:
    return group_data_cache.get(str(chat_id), {}).get("next_deadline", {})


def get_group_streaks(chat_id: int) -> dict[str, int]:
    return group_data_cache.get(str(chat_id), {}).get("streaks", {})


def get_all_groups():
    return group_data_cache.keys()


def set_last_reminder(chat_id: int, timestamp: int):
    str_chat = str(chat_id)
    if str_chat not in group_data_cache:
        group_data_cache[str_chat] = {}
    group = group_data_cache[str_chat]
    group["last_reminder"] = timestamp
    write_group_data()


def get_last_reminder(chat_id: int) -> int | None:
    str_chat = str(chat_id)
    group = group_data_cache.get(str_chat, None)
    if group is None:
        return None
    return group.get("last_reminder", 0)
