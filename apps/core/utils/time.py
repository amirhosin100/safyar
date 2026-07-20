import datetime
import jdatetime
from django.utils.dateparse import parse_datetime


def get_time(year, month, open_time, closed_time, week_days):
    start_date = datetime.datetime(month=month, year=year, day=1)
    times = {}

    while start_date.month == month:
        time = open_time.replace(second=0, microsecond=0)
        str_time = start_date.strftime("%Y-%m-%d")
        times[str_time] = set()

        if start_date.weekday() in week_days:
            start_date += datetime.timedelta(days=1)
            continue

        while time < closed_time:
            times[str_time].add(time.strftime("%H:%M"))
            minutes = time.minute + time.hour * 60 + 30
            time = datetime.time(minute=minutes % 60, hour=minutes // 60)

        start_date += datetime.timedelta(days=1)

    return times


def to_persian_date(date):
    if isinstance(date,str):
        date = parse_datetime(date)

    date = jdatetime.date.fromgregorian(date=date)
    return date.strftime("%Y/%m/%d %H:%M")
