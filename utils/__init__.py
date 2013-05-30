import datetime

def seconds_timesince(value):
    if not value:
        return 0
    now = datetime.datetime.utcnow()
    delta = now - value

    return delta.days * 24 * 60 * 60 + delta.seconds