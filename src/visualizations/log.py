from datetime import datetime


def log(msg):
    """
    Log message
    """
    print(f"{datetime.now().strftime('%H:%M:%S')}: {msg}")
