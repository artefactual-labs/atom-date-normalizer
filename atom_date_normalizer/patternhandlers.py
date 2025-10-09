# -*- coding: utf-8 -*-

"""Pattern Handlers

This pattern handlers script identifies different date formats that may be
supplied to it and attempts to return an ISO version of the date to the caller.
The return in all cases is a tuple: (start date, end date).
"""

import calendar
import re
import sys

from datetime import datetime
from inspect import getmembers, isfunction


class NormalizeDateException(Exception):
    pass


patterns = []

# Some simple replace() substitutions to clean the data up before parsing
subs = (
    ("[", ""),
    ("]", ""),
    ("ca.", ""),
    ("ca", ""),
    ("-?", "-"),
    ("cir", ""),
    (",", ""),
    (".", ""),
)

# Regular expression substitutes.
re_subs = (
    (r"\bsept\b", "september"),
    (r"\bjan\b", "january"),
    (r"\bfeb\b", "february"),
    (r"\bmar\b", "march"),
    (r"\bapr\b", "april"),
    (r"\bjun\b", "june"),
    (r"\bjul\b", "july"),
    (r"\baug\b", "august"),
    (r"\bsep\b", "september"),
    (r"\boct\b", "october"),
    (r"\bnov\b", "november"),
    (r"\bdec\b", "december"),
)


long_months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

short_months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def add_patterns():
    global patterns
    for handler, _ in getmembers(sys.modules[__name__], isfunction):
        if handler.startswith("pattern"):
            fn = globals()[handler]
            if hasattr(fn, "__regex__"):
                patterns.append((getattr(fn, "__regex__"), fn))
            else:
                raise AttributeError(
                    'Function "{}" does not have the required regular expression pattern defined. '
                    "Please ensure you specify a regex pattern with the @regex decorator for pattern "
                    "handlers.".format(handler)
                )


def date_clean(date_str):
    """Clean the date using various techniques to better improve searching."""
    date_str = date_str.strip().lower()
    # Perform standard string replacements.
    for junk, replacement in subs:
        date_str = date_str.replace(junk, replacement)
    # Perform regular expression replacements.
    for junk, replacement in re_subs:
        date_str = re.sub(junk, replacement, date_str)
    return date_str.strip()


def date_parse(date_str):
    for pattern, handler in patterns:
        match = re.search(pattern, date_str)
        if match:
            return handler(date_str, match)

    # Capitalize the characters in the string.
    date_str = date_str.title()

    # These options are fall-back options where Regex is a little harder to
    # create for all the options.
    for month in long_months:
        if month in date_str:
            try:
                return normalize_year_month_day(date_str)
            except ValueError:
                pass
            try:
                return normalize_year_month(date_str)
            except ValueError:
                pass
            try:
                return normalize_month_year(date_str)
            except ValueError:
                pass
            try:
                return normalize_month_day_year(date_str)
            except ValueError:
                pass
    raise NormalizeDateException(
        "DATE NOT NORMALIZED: No match found: {}".format(date_str)
    )


# Custom date parsing where the regex parsers might not suit our purposes.
def normalize_year_month_day(date_str):
    """Normalize YYYY Long Month Name Day date strings."""
    try:
        parsed_date = datetime.strptime(date_str, "%Y %B %d")
    except ValueError:
        parsed_date = datetime.strptime(date_str, "%Y %B%d")
    return (parsed_date.strftime("%Y-%m-%d"), None)


def normalize_year_month(date_str):
    """Normalize YYYY Long Month Name date strings."""
    parsed_date = datetime.strptime(date_str, "%Y %B")
    _, eom = calendar.monthrange(parsed_date.year, parsed_date.month)
    return (
        "{}-01".format(parsed_date.strftime("%Y-%m")),
        "{}-{}".format(parsed_date.strftime("%Y-%m"), eom),
    )


def normalize_month_year(date_str):
    """Normalize Long Month Name YYYY strings."""
    parsed_date = datetime.strptime(date_str, "%B %Y")
    _, eom = calendar.monthrange(parsed_date.year, parsed_date.month)
    return (
        "{}-01".format(parsed_date.strftime("%Y-%m")),
        "{}-{}".format(parsed_date.strftime("%Y-%m"), eom),
    )


def normalize_month_day_year(date_str):
    """Normalize Long Month Name Day YYYY strings."""
    parsed_date = datetime.strptime(date_str, "%B %d %Y")
    return (parsed_date.strftime("%Y-%m-%d"), None)


# Context manager enabling out regular expression decorator.
def regex(pattern):
    def decorate(func):
        setattr(func, "__regex__", pattern)
        return func

    return decorate


# Individual regular expression date handlers.
@regex(r"[Bb]etween (\d{4}) [Aa]nd (\d{4})")
def pattern1(date_str, match):
    """'Between 1900 and 2000' = '1900-01-01', '2000-12-31'"""
    return (match.group(1) + "-01-01", match.group(2) + "-12-31")


@regex(r"^(\d{3})-$")
def pattern2(date_str, match):
    """'195-' = '1950-01-01', '1959-12-31'"""
    return (match.group(1) + "0-01-01", match.group(1) + "9-12-31")


@regex(r"[Aa]fter (\d{4})")
def pattern3(date_str, match):
    """'After 1900' = '1900-12-31', None"""
    return (match.group(1) + "-12-31", None)


@regex(r"[Bb]efore (\d{4})")
def pattern4(date_str, match):
    """'Before 1900' = None, '1900-01-01'"""
    return (None, match.group(1) + "-01-01")


@regex(r"(\d{4}) or (\d{4})")
def pattern5(date_str, match):
    """'1950 or 1951' = '1950-01-01', '1951-12-31'"""
    return (match.group(1) + "-01-01", match.group(2) + "-12-31")


@regex(r"(\d{4})\?")
def pattern6(date_str, match):
    """'1950?' = '1950-01-01', '1950-12-31'"""
    return (match.group(1) + "-01-01", match.group(1) + "-12-31")


@regex(r"^(\d{4})\'?[-s]$")
def pattern7(date_str, match):
    """'1950-' | '1950s' | '1950''s' = '1950-01-01', '1959-12-31'"""
    return (match.group(1) + "-01-01", match.group(1)[:-1] + "9-12-31")


@regex(r"^(\d{2})[?-]{1,2}$")
def pattern8(date_str, match):
    """'19-' = '1900-01-01', '1999-12-31'"""
    return (match.group(1) + "00-01-01", match.group(1) + "99-12-31")


@regex(r"^(\d{2})---(\d{2})--$")
def pattern9(date_str, match):
    """'18---19--' = '1800-01-01', '1999-12-31'"""
    return (match.group(1) + "00-01-01", match.group(2) + "99-12-31")


@regex(r"^(\d{3})--(\d{2})--$")
def pattern10(date_str, match):
    """'183--19--' = '1830-01-01', '1999-12-31'"""
    return (match.group(1) + "0-01-01", match.group(2) + "99-12-31")


@regex(r"^(\d{2})---(\d{3})-$")
def pattern11(date_str, match):
    """'18---194-' = '1800-01-01', '1949-12-31'"""
    return (match.group(1) + "00-01-01", match.group(2) + "9-12-31")


@regex(r"^(\d{4})-(\d{2})--$")
def pattern12(date_str, match):
    """'1834-19--' = '1834-01-01', '1999-12-31'"""
    return (match.group(1) + "-01-01", match.group(2) + "99-12-31")


@regex(r"^(\d{2})---(\d{4})$")
def pattern13(date_str, match):
    """'18---1945' = '1800-01-01', '1945-12-31'"""
    return (match.group(1) + "00-01-01", match.group(2) + "-12-31")


@regex(r"^(\d{3})--(\d{3})-$")
def pattern14(date_str, match):
    """'195--196-' = '1950-01-01', '1969-12-31'"""
    return (match.group(1) + "0-01-01", match.group(2) + "9-12-31")


@regex(r"^(\d{4})-(\d{3})-$")
def pattern15(date_str, match):
    """'1955-196-' = '1955-01-01', '1969-12-31'"""
    return (match.group(1) + "-01-01", match.group(2) + "9-12-31")


@regex(r"^(\d{3})--(\d{4})$")
def pattern16(date_str, match):
    """'195--1960' = '1950-01-01', '1960-12-31'"""
    return (match.group(1) + "0-01-01", match.group(2) + "-12-31")


# Added for HMM


@regex(r"^(\d{4})(\s)?-(\s)?(\d{4})$")
def pattern17(date_str, match):
    """Match a yyyy-yyyy string and return the YYYY-01-01 to YYYY-12-31. If
    there is a space between the dash, we'll match that as well, e.g.
    yyyy - yyyy.
    """
    return ("{}-01-01".format(match.group(1)), "{}-12-31".format(match.group(4)))


@regex(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
def pattern18(date_str, match):
    """Match mm/dd/yyyy or at some risk dd/mm/yyyy and return yyyy-mm-dd."""
    parsed_date = datetime.strptime(date_str, "%m/%d/%Y")
    return (parsed_date.strftime("%Y-%m-%d"), None)


@regex(r"^(\d{1,2})/(\d{1,2})/(\d{2})$")
def pattern19(date_str, match):
    """Match mm/dd/yy or at some risk dd/mm/yy and return yyyy-mm-dd."""
    parsed_date = datetime.strptime(date_str, "%m/%d/%y")
    return (parsed_date.strftime("%Y-%m-%d"), None)


@regex(r"^(\d{1,2})/(\d{1,2})/(\d{4})\s(\d{1,2})/(\d{1,2})/(\d{4})$")
def pattern20(date_str, match):
    """Match mm/dd/yyyy dd/mm/yyyy and return yyyy-mm-dd yy-mm-dd."""
    parsed_date_one = datetime.strptime(date_str.split(" ")[0], "%m/%d/%Y")
    parsed_date_two = datetime.strptime(date_str.split(" ")[1], "%m/%d/%Y")
    return (parsed_date_one.strftime("%Y-%m-%d"), parsed_date_two.strftime("%Y-%m-%d"))


@regex(r"^(\d{4})$")
def pattern21(date_str, match):
    """Match a simple YYYY format and return the date range for the year."""
    return ("{}-01-01".format(match.group(1)), "{}-12-31".format(match.group(1)))


@regex(r"^(\d{4})\s(\d{4})$")
def pattern22(date_str, match):
    """Match a yyyy yyyy string and return the YYYY-01-01 to YYYY-12-31. Note
    the space in between the two years.
    """
    return ("{}-01-01".format(match.group(1)), "{}-12-31".format(match.group(2)))


@regex(r"^(\d{4})[-\s]?([a-z]+)\s+(\d{4})[-\s]?([a-z]+)$")
def pattern23(date_str, match):
    """Match strings like '2000-Mar 2000-Mar' (after cleaning becomes '2000-march 2000-march')
    and return the full month span as ISO dates: 'YYYY-MM-01', 'YYYY-MM-<last day>'.

    Also supports differing end month, e.g., '2000-Mar 2000-Apr' -> '2000-03-01', '2000-04-30'.
    """
    y1 = int(match.group(1))
    m1_name = match.group(2).lower()
    y2 = int(match.group(3))
    m2_name = match.group(4).lower()

    month_lookup = {calendar.month_name[i].lower(): i for i in range(1, 13)}

    if m1_name not in month_lookup or m2_name not in month_lookup:
        raise NormalizeDateException(
            "DATE NOT NORMALIZED: Unknown month name(s) in '{}'".format(date_str)
        )

    m1 = month_lookup[m1_name]
    m2 = month_lookup[m2_name]

    # Start is first day of first month
    start = f"{y1}-{m1:02d}-01"
    # End is last day of second month
    _, eom2 = calendar.monthrange(y2, m2)
    end = f"{y2}-{m2:02d}-{eom2:02d}"

    return (start, end)


@regex(r"^(\d{4})[-\s]?([a-z]+)[-\s]?(\d{1,2})\s+(\d{4})[-\s]?([a-z]+)[-\s]?(\d{1,2})$")
def pattern24(date_str, match):
    """Match strings like '2001-Nov-22 2001-Nov-23' (after cleaning becomes
    '2001-november-22 2001-november-23') and return precise ISO start/end dates
    'YYYY-MM-DD', 'YYYY-MM-DD'. Also supports differing months and days, e.g.,
    '2000-Mar-14 2000-Apr-18' -> '2000-03-14', '2000-04-18'.
    """

    y1 = int(match.group(1))
    m1_name = match.group(2).lower()
    d1 = int(match.group(3))
    y2 = int(match.group(4))
    m2_name = match.group(5).lower()
    d2 = int(match.group(6))

    month_lookup = {calendar.month_name[i].lower(): i for i in range(1, 13)}

    if m1_name not in month_lookup or m2_name not in month_lookup:
        raise NormalizeDateException(
            "DATE NOT NORMALIZED: Unknown month name(s) in '{}'".format(date_str)
        )

    m1 = month_lookup[m1_name]
    m2 = month_lookup[m2_name]

    # Validate dates by constructing datetime objects
    try:
        start_dt = datetime(y1, m1, d1)
        end_dt = datetime(y2, m2, d2)
    except ValueError:
        raise NormalizeDateException(
            "DATE NOT NORMALIZED: Invalid day for month/year in '{}'".format(date_str)
        )

    start = start_dt.strftime("%Y-%m-%d")
    end = end_dt.strftime("%Y-%m-%d")

    return (start, end)


@regex(
    r"^(\d{4})[-\s]?([a-z]+)(?:[-\s]?(\d{1,2}))?\s+(\d{4})[-\s]?([a-z]+)(?:[-\s]?(\d{1,2}))?$"
)
def pattern25(date_str, match):
    """Match mixed specificity ranges like:
    - '1997-October 1998-June-04' -> '1997-10-01', '1998-06-04'
    - '1992-August 1993-July-09' -> '1992-08-01', '1993-07-09'
    - '1992-Aug 1993-Jul-09' -> '1992-08-01', '1993-07-09' (after cleaning)

    Start day defaults to 01 when absent; end day defaults to month end when absent.
    """

    y1 = int(match.group(1))
    m1_name = match.group(2).lower()
    d1_str = match.group(3)
    y2 = int(match.group(4))
    m2_name = match.group(5).lower()
    d2_str = match.group(6)

    month_lookup = {calendar.month_name[i].lower(): i for i in range(1, 13)}

    if m1_name not in month_lookup or m2_name not in month_lookup:
        raise NormalizeDateException(
            "DATE NOT NORMALIZED: Unknown month name(s) in '{}'".format(date_str)
        )

    m1 = month_lookup[m1_name]
    m2 = month_lookup[m2_name]

    # Determine start day: default to 1 if absent
    d1 = int(d1_str) if d1_str is not None else 1
    # Determine end day: default to last day of month if absent
    if d2_str is None:
        _, eom2 = calendar.monthrange(y2, m2)
        d2 = eom2
    else:
        d2 = int(d2_str)

    # Validate by constructing datetimes
    try:
        start_dt = datetime(y1, m1, d1)
        end_dt = datetime(y2, m2, d2)
    except ValueError:
        raise NormalizeDateException(
            "DATE NOT NORMALIZED: Invalid day for month/year in '{}'".format(date_str)
        )

    return (start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))


@regex(r"^(\d{4})\s+(\d{4})[-\s]?([a-z]+)(?:[-\s]?(\d{1,2}))?$")
def pattern26(date_str, match):
    """Match year-only start with a year-month or year-month-day end, e.g.:
    - '1991 1993-May-05' -> '1991-01-01', '1993-05-05'
    - '1991 1993-May'    -> '1991-01-01', '1993-05-31' (last day of May)

    Start date defaults to January 1 when only a year is given.
    """

    y1 = int(match.group(1))
    y2 = int(match.group(2))
    m2_name = match.group(3).lower()
    d2_str = match.group(4)

    month_lookup = {calendar.month_name[i].lower(): i for i in range(1, 13)}
    if m2_name not in month_lookup:
        raise NormalizeDateException(
            "DATE NOT NORMALIZED: Unknown month name in '{}'".format(date_str)
        )

    m2 = month_lookup[m2_name]

    # End day: explicit or last day of month
    if d2_str is None:
        _, eom2 = calendar.monthrange(y2, m2)
        d2 = eom2
    else:
        d2 = int(d2_str)

    # Validate end date; start is always Jan 1
    try:
        end_dt = datetime(y2, m2, d2)
    except ValueError:
        raise NormalizeDateException(
            "DATE NOT NORMALIZED: Invalid day for month/year in '{}'".format(date_str)
        )

    start = f"{y1}-01-01"
    end = end_dt.strftime("%Y-%m-%d")

    return (start, end)


@regex(r"^(\d{3})\s*-\s*(\d{3})\s*-$")
def pattern27(date_str, match):
    """Match two decade-like 3-digit ranges separated by space, e.g.:
    - '198- 199-' -> '1980-01-01', '1999-12-31'

    Interprets '198-' as 1980s and '199-' as 1990s.
    """
    start_prefix = match.group(1)
    end_prefix = match.group(2)
    return (
        f"{start_prefix}0-01-01",
        f"{end_prefix}9-12-31",
    )

add_patterns()

