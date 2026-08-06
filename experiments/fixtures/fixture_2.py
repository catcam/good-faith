import os


def save_if_new(path, content):
    try:
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(content)
            return True
    except Exception:
        pass
    return False
