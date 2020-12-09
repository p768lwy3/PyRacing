from datetime import date, timedelta
from typing import Dict, List, Union


def get_day_of_week(year: int, dow: int) -> List[date]:
    """Get all the days of the given day of week.

    :param year: year to be get.
    :param dow: day of week. From Monday = 0 to Sunday = 6.
    :return:
    """
    new_year = date(year, 1, 1)
    start_date = new_year + timedelta(days=dow - new_year.weekday())
    start_date = start_date + timedelta(days=7) if start_date < new_year else start_date

    dates = []
    while start_date.year == year:
        dates.append(start_date)
        start_date += timedelta(days=7)
    return dates


def parse_cookies(cookies: Union[int, List[Union[int, str]]]) -> Dict[str, str]:
    parsed = []
    for cookie in cookies:
        parsed.append([cookie['name'], cookie['value']])
    parsed = dict(parsed)
    return parsed
