from datetime import datetime


def now():
    return datetime.utcnow().replace(microsecond=0)

def timestamp(time):
    unixEpoch = datetime.utcfromtimestamp(0)
    return int((time - unixEpoch).total_seconds())
