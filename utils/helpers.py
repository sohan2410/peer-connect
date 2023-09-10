def find_in_dict(data, key, value):
    for item in data:
        if item[key] == value:
            return item
    return None
