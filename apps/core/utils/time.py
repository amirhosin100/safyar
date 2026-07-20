import datetime

import jdatetime
from django.utils.dateparse import parse_datetime


def get_time(year, month, open_time, closed_time, week_days):
    start_date = datetime.datetime(month=month, year=year, day=1)
    times = {}
    now = datetime.datetime.now()
    now_time = datetime.time(hour=now.hour, minute=now.minute)

    while start_date.month == month:
        str_time = start_date.strftime("%Y-%m-%d")
        times[str_time] = []

        if start_date.weekday() in week_days or start_date < now - datetime.timedelta(days=1):
            start_date += datetime.timedelta(days=1)
            continue

        time = open_time.replace(second=0, microsecond=0)
        while time < closed_time:
            if time < now_time and start_date < now:
                time = add_30_minutes(time)
                continue
            times[str_time].append(time.strftime("%H:%M"))
            time = add_30_minutes(time)

        start_date += datetime.timedelta(days=1)

    return times


def to_persian_date(date):
    if isinstance(date,str):
        date = parse_datetime(date)

    date = jdatetime.date.fromgregorian(date=date)
    return date.strftime("%Y/%m/%d %H:%M")

def add_30_minutes(time):
    minutes = time.minute + time.hour * 60 + 30
    return datetime.time(minute=minutes % 60, hour=minutes // 60)
