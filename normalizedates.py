#!/usr/bin/env python3

""" This script will read in a CSV file and transform any date strings into AtoM readable start and end dates whenever
    possible. A CSV will be outputted indicating the original date string, and the AtoM compatible start/end dates """

import argparse
import csv
import re
import sys

from datetime import datetime

from atomdatenormalizer.patternhandlers import date_clean
from atomdatenormalizer.patternhandlers import date_parse
import atomdatenormalizer.vendor.daterangeparser

def is_sane_date(date_range, min_year=1000, max_year=2100):
    """ Check whether date range normalization is within a somewhat sane year range """

    if not date_range:
        return False

    try:
        end_datetime = None
        start_datetime = None

        # Convert to datetime temporarily via strptime, which will toss ValueError if not 1 <= year <= 9999
        # Note that start date can be 'None' - e.g. in the case of 'before 1976'.
        if isinstance(date_range[0], str):
            start_datetime = datetime.strptime(date_range[0], '%Y-%m-%d')

        # It's possible to have the end date range set to None if there is no end range, only
        # check date validity (via strptime) if we've got a string to deal with.
        if isinstance(date_range[1], str):
            end_datetime = datetime.strptime(date_range[1], '%Y-%m-%d')

        # Also some manual checking to see if the year is within a specified 'sane' date range.
        result = True
        if start_datetime:
            result = min_year <= start_datetime.year <= max_year
        if end_datetime:
            result = result and (min_year <= end_datetime.year <= max_year)

    except ValueError as e:
        return False

    return result


def parse_date_string(date_str):
    """ Given a date string, attempt to normalize it into AtoM compatible start / end dates.

        :param date_string: Unnormalized date string.
        :return: None if this function fails to normalize the date string, otherwise return a list with three
                 elements: (originalDateString, normalizedStartDateString, normalizedEndDateString)
    """
    date_str_clean = date_clean(date_str)  # Remove junk around dates

    try:
        # First attempt to parse the date range via the daterangeparser library
        # It will return two datetime objects specifying start/end range, we can use strftime to convert to string.
        r = atomdatenormalizer.vendor.daterangeparser.parse(date_str_clean)
        r = [dt.strftime('%Y-%m-%d') if isinstance(dt, datetime) else dt for dt in r]  # Convert any datetimes to strings (YYYY-MM-DD)

    except Exception as e:
        # daterangeparser cannot parse the date range, attempt to use our regex pattern matching / handler functions
        r = date_parse(date_str_clean)

    if is_sane_date(r):
        return [date_str, r[0], r[1]]
    return None


def parse_csv(args):
    """ Iterate a CSV's date strings and normalize them into an AtoM compatible format, output resulting
        start / end dates to specified output CSV.

        :param args: Command line arguments parsed from argparse.
    """
    results = []

    with open(args.csv) as f:
        malformed_dates = []

        reader = csv.DictReader(f)

        if args.column not in reader.fieldnames:
            print('Date string column "{}" not found in CSV, if you are using a custom column name for your date '
                  'strings, use the -c option to specify the custom name.'.format(args.column))
            sys.exit(1)

        for record in reader:
            date_str = record.get(args.column, '').strip()
            if not date_str:
                continue

            r = parse_date_string(date_str)
            if r:
                results.append(r)

            if not r and args.error_log:
                malformed_dates.append(date_str)

        handle_error_log(args, malformed_dates)
    return results


def write_csv(args, results):
    with open(args.output, 'w') as f:
        w = csv.writer(f)
        w.writerow(('originalDateString', 'startDate', 'endDate'))
        w.writerows(results)


def handle_error_log(args, malformed_dates):
    """ If user specified an error log path, write any dates we were unable to normalize to said path.

        :param args: Command line arguments parsed from argparse.
        :param malformed_dates: A list containing date strings we were unable to normalize.
    """
    if not args.error_log:
        return

    with open(args.error_log, 'w') as f:
        print('invalidDates', file=f)
        for date_str in malformed_dates:
            print(date_str, file=f)


def get_args():
    """ Parse CLI arguments via argparse and return the results.

        :return: Namespace object containing the various CLI args/opts as attributes (e.g.: ret.csv)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', help='Path to input CSV containing date strings')
    parser.add_argument('-e', '--error-log', help='Specify an error log listing all date strings that failed to parse')
    parser.add_argument('-o', '--output', default='normalized_dates.csv', help='Path to output CSV with parsed dates')
    parser.add_argument('-c', '--column', default='Dates',
                        help='Specify column name for date strings in inputted CSV (defaults to "Dates")')

    return parser.parse_args()


def main():
    results = parse_csv(get_args())
    write_csv(get_args(), results)


if __name__ == '__main__':
    sys.exit(main())
