class ErrorStorage:
    error_list = {}


def get_error_key(topic, part, code_index):
    return f"{topic}_{part}_{code_index}"


def store_error(key, error):
    ErrorStorage.error_list[key] = error


def clear_error(key):
    if key not in ErrorStorage.error_list:
        return
    del ErrorStorage.error_list[key]


def get_error(key):
    if key not in ErrorStorage.error_list:
        return None
    return ErrorStorage.error_list[key]
