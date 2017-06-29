import calendar
import re
import sys

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


@regex(r'^(\d{4})[-s]$')
def pattern7(date_str, match):
    """ '1950-' | '1950s' = '1950-01-01', '1959-12-31' """
    return (match.group(1) + '-01-01', match.group(1)[:-1] + '9-12-31')


@regex(r'(\d{2})[?-]{1,2}')
def pattern8(date_str, match):
    """ '19-' = '1900-01-01', '1999-12-31' """
    return (match.group(1) + '00-01-01', match.group(1) + '99-12-31')


add_patterns()
