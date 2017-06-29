import calendar
import re

patterns = []

# Some simple replace() substitutions to clean the data up before parsing
subs = (
    ('[', ''),
    (']', ''),
    ('ca.', ''),
    ('ca', ''),
    ('-?', '-'),
)


def add_pattern(pattern, transform_handler):
    global patterns
    patterns.append((pattern, transform_handler))


def date_clean(date_str):
    for junk, replacement in subs:
        date_str = date_str.replace(junk, replacement)

    return date_str.strip()


def date_parse(date_str):
    for pattern, handler in patterns:
        match = re.search(pattern, date_str)
        if match:
            return handler(date_str, match)


#-----------------------------------------------------------------------------------------

def pattern1(date_str, match):
    return (match.group(1) + '-01-01', match.group(2) + '-12-31')


def pattern2(date_str, match):
    return (match.group(1) + '0-01-01', match.group(1) + '9-12-31')


def pattern3(date_str, match):
    return (match.group(1) + '-12-31', None)


def pattern4(date_str, match):
    return (None, match.group(1) + '-01-01')


def pattern5(date_str, match):
    return (match.group(1) + '-01-01', match.group(2) + '-12-31')


def pattern6(date_str, match):
    return (match.group(1) + '-01-01', match.group(1) + '-12-31')


def pattern7(date_str, match):
    return (match.group(1) + '-01-01', match.group(1)[:-1] + '9-12-31')


def pattern8(date_str, match):
    return (match.group(1) + '00-01-01', match.group(1) + '99-12-31')


add_pattern(r'[Bb]etween (\d{4}) [Aa]nd (\d{4})', pattern1)  # "Between 1900 and 2000" = 1900-01-01 - 2000-12-31
add_pattern(r'^(\d{4})[-s]$', pattern7)                      # "1950-"|"1950s" = 1950-01-01 - 1959-12-31
add_pattern(r'^(\d{3})-$', pattern2)                         # "195-" = 1950-01-01 - 1959-12-31
add_pattern(r'[Aa]fter (\d{4})', pattern3)                   # "After 1900" = 1900-12-31 - None
add_pattern(r'[Bb]efore (\d{4})', pattern4)                  # "Before 1900" = None - 1900-01-01
add_pattern(r'(\d{4}) or (\d{4})', pattern5)                 # "1950 or 1951" = 1950-01-01 - 1951-12-31
add_pattern(r'(\d{4})\?', pattern6)                          # "1950?" = 1950-01-01 - 1950-12-31
add_pattern(r'(\d{2})[?-]{1,2}', pattern8)                   # "19-" = 1900-01-01 - 1999-12-31
