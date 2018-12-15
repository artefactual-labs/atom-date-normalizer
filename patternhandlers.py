import calendar
import re
import sys
import datetime

from inspect import getmembers, isfunction

patterns = []

# Some simple replace() substitutions to clean the data up before parsing
subs = (
    ('[', ''),
    (']', ''),
    ('ca.', ''),
    ('ca', ''),
    ('-?', '-'),
)


def add_patterns():
    global patterns
    for handler, _ in getmembers(sys.modules[__name__], isfunction):
        if handler.startswith('pattern'):
            fn = globals()[handler]
            if hasattr(fn, '__regex__'):
                patterns.append((getattr(fn, '__regex__'), fn))
            else:
                raise AttributeError('Function "{}" does not have the required regular expression pattern defined. '
                                     'Please ensure you specify a regex pattern with the @regex decorator for pattern '
                                     'handlers.'.format(handler))


def date_clean(date_str):
    for junk, replacement in subs:
        date_str = date_str.replace(junk, replacement)

    return date_str.strip()


def date_parse(date_str):
    for pattern, handler in patterns:
        match = re.search(pattern, date_str)
        if match:
            return handler(date_str, match)


def regex(pattern):
    def decorate(func):
        setattr(func, '__regex__', pattern)
        return func
    return decorate

#-----------------------------------------------------------------------------------------

@regex(r'[Bb]etween (\d{4}) [Aa]nd (\d{4})')
def pattern1(date_str, match):
    """ 'Between 1900 and 2000' = '1900-01-01', '2000-12-31' """
    return (match.group(1) + '-01-01', match.group(2) + '-12-31')


@regex(r'^(\d{3})-$')
def pattern2(date_str, match):
    """ '195-' = '1950-01-01', '1959-12-31' """
    return (match.group(1) + '0-01-01', match.group(1) + '9-12-31')


@regex(r'[Aa]fter (\d{4})')
def pattern3(date_str, match):
    """ 'After 1900' = '1900-12-31', None """
    return (match.group(1) + '-12-31', None)


@regex(r'[Bb]efore (\d{4})')
def pattern4(date_str, match):
    """ 'Before 1900' = None, '1900-01-01' """
    return (None, match.group(1) + '-01-01')


@regex(r'(\d{4}) or (\d{4})')
def pattern5(date_str, match):
    """ '1950 or 1951' = '1950-01-01', '1951-12-31' """
    return (match.group(1) + '-01-01', match.group(2) + '-12-31')


@regex(r'(\d{4})\?')
def pattern6(date_str, match):
    """ '1950?' = '1950-01-01', '1950-12-31' """
    return (match.group(1) + '-01-01', match.group(1) + '-12-31')


@regex(r'^(\d{4})\'?[-s]$')
def pattern7(date_str, match):
    """ '1950-' | '1950s' | '1950''s' = '1950-01-01', '1959-12-31' """
    return (match.group(1) + '-01-01', match.group(1)[:-1] + '9-12-31')


@regex(r'^(\d{2})[?-]{1,2}$')
def pattern8(date_str, match):
    """ '19-' = '1900-01-01', '1999-12-31' """
    return (match.group(1) + '00-01-01', match.group(1) + '99-12-31')


@regex(r'^(\d{2})---(\d{2})--$')
def pattern9(date_str, match):
    """ '18---19--' = '1800-01-01', '1999-12-31' """
    return (match.group(1) + '00-01-01', match.group(2) + '99-12-31')


@regex(r'^(\d{3})--(\d{2})--$')
def pattern10(date_str, match):
    """ '183--19--' = '1830-01-01', '1999-12-31' """
    return (match.group(1) + '0-01-01', match.group(2) + '99-12-31')


@regex(r'^(\d{2})---(\d{3})-$')
def pattern11(date_str, match):
    """ '18---194-' = '1800-01-01', '1949-12-31' """
    return (match.group(1) + '00-01-01', match.group(2) + '9-12-31')


@regex(r'^(\d{4})-(\d{2})--$')
def pattern12(date_str, match):
    """ '1834-19--' = '1834-01-01', '1999-12-31' """
    return (match.group(1) + '-01-01', match.group(2) + '99-12-31')


@regex(r'^(\d{2})---(\d{4})$')
def pattern13(date_str, match):
    """ '18---1945' = '1800-01-01', '1945-12-31' """
    return (match.group(1) + '00-01-01', match.group(2) + '-12-31')


@regex(r'^(\d{3})--(\d{3})-$')
def pattern14(date_str, match):
    """ '195--196-' = '1950-01-01', '1969-12-31' """
    return (match.group(1) + '0-01-01', match.group(2) + '9-12-31')


@regex(r'^(\d{4})-(\d{3})-$')
def pattern15(date_str, match):
    """ '1955-196-' = '1955-01-01', '1969-12-31' """
    return (match.group(1) + '-01-01', match.group(2) + '9-12-31')


@regex(r'^(\d{3})--(\d{4})$')
def pattern16(date_str, match):
    """ '195--1960' = '1950-01-01', '1960-12-31' """
    return (match.group(1) + '0-01-01', match.group(2) + '-12-31')


@regex(r'^(\d{4}-\d{2}-\d{2})$')
def pattern17(date_str, match):
    """ '1995-10-20' = '1995-10-20', '1995-10-20' """
    return (match.group(1), match.group(1))


@regex(r'^\?-(\d{4})$')
def pattern18(date_str, match):
    """ '?-1922' = '1922-01-01', '1922-12-31' """
    return (match.group(1) + '-01-01', match.group(1) + '-12-31')


@regex(r'^(\d{4}),\s*(\d{4})$')
def pattern19(date_str, match):
    """ '1918, 1922' = '1918-01-01', '1922-12-31' """
    return (match.group(1) + '-01-01', match.group(1) + '-12-31')


@regex(r'^(\d{4})-(\d{4})\'?[-s]$')
def pattern20(date_str, match):
    """ '1976-1985-' | '1976-1985s' | '1976-1985''s' = '1976-01-01', '1985-12-31' """
    return (match.group(1) + '-01-01', match.group(2) + '-12-31')


@regex(r'^(\d{4})-*$')
def pattern21(date_str, match):
    """ '1976-' | '1976--' | '1976---' = '1976-01-01', '1976-12-31' """
    return (match.group(1) + '-01-01', match.group(1) + '-12-31')


@regex(r'^([a-zA-Z]*\s+\d{1,2},\s+\d{4})-([a-zA-Z]*\s+\d{1,2},\s+\d{4})$')
def pattern22(date_str, match):
    """ 'July 5, 1905-May 27, 2000' = '1905-07-05', '2000-05-27' """
    date1 = datetime.datetime.strptime(match.group(1), "%B %d, %Y").date()
    date2 = datetime.datetime.strptime(match.group(2), "%B %d, %Y").date()
    return (date1.isoformat(), date2.isoformat())


@regex(r'^(\d{4})-(\d{2})$')
def pattern23(date_str, match):
    """ '1834-08' = '1834-08-01', '1834-08-31' """
    return (match.group(1) + '-' + match.group(2) + '-01', match.group(1) + '-' + match.group(2) + '-' + str(calendar.monthrange(int(match.group(1)), int(match.group(2)))[1]))


@regex(r'^(\d{4}-\d{2}).*to.*(\d{4})-(\d{2})$')
def pattern24(date_str, match):
    """ '2006-01 to 2006-12' = '2006-01-01', '2006-12-31' """
    return (match.group(1) + '-01', match.group(2) + '-' + match.group(3) + '-' + str(calendar.monthrange(int(match.group(2)), int(match.group(3)))[1]))


@regex(r'^(\d{4}-\d{2}).*to.*(\d{4}-\d{2}-\d{2})$')
def pattern25(date_str, match):
    """ '2006-01 to 2006-12-16' = '2006-01-01', '2006-12-16' """
    return (match.group(1) + '-01', match.group(2))


@regex(r'^(\d{4}-\d{2}-\d{2}).*to.*(\d{4})-(\d{2})$')
def pattern26(date_str, match):
    """ '2006-01-18 to 2006-12' = '2006-01-18', '2006-12-16' """
    return (match.group(1), match.group(2) + '-' + match.group(3) + '-' + str(calendar.monthrange(int(match.group(2)), int(match.group(3)))[1]))


@regex(r'^(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})$')
def pattern27(date_str, match):
    """ '1930-04-03 to 1989-07-05' = '1930-04-03', '1989-07-05' """
    return (match.group(1), match.group(2))


@regex(r'(\d{4})\s+(or|and)\s+[Aa]fter')
def pattern28(date_str, match):
    """ '1900 or after' = '1900-12-31', None """
    return (match.group(1) + '-12-31', None)


@regex(r'(\d{4})\s+(or|and)\s+[Bb]efore')
def pattern29(date_str, match):
    """ '1900 or before' = None, '1900-01-01' """
    return (None, match.group(1) + '-01-01')


@regex(r'(\d{4}-\d{2}-\d{2})\s+(and|or)\s+[Aa]fter')
def pattern30(date_str, match):
    """ '1923-02-27 or after' = '1923-02-27', None """
    return (match.group(1), None)


@regex(r'(\d{4}-\d{2}-\d{2})\s+(and|or)\s+[Bb]efore')
def pattern31(date_str, match):
    """ '1923-02-27 or before' = None, '1923-02-27' """
    return (None, match.group(1))

add_patterns()
