import csv
from pathlib import Path

import pytest

from atom_date_normalizer.normalizedates import parse_date_string


def load_cases():
    fixture = Path(__file__).parent / "fixtures" / "atom_date_cases.csv"
    with fixture.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            input_str = row["input"].strip()
            exp_start = row["expected_start"].strip() or None
            exp_end = row["expected_end"].strip() or None
            yield input_str, exp_start, exp_end


cases = [
    pytest.param(
        i,
        s,
        e,
        id=f"{(i[:50] + '...') if len(i) > 50 else i} -> {s or 'None'}, {e or 'None'}",
    )
    for i, s, e in load_cases()
]


@pytest.mark.integration
@pytest.mark.parametrize("input_str,exp_start,exp_end", cases)
def test_parse_date_string_cases(input_str, exp_start, exp_end):
    res = parse_date_string(input_str)

    if exp_start is None and exp_end is None:
        assert res is None
        return

    assert res is not None, f"Expected a result for: {input_str}"
    # parse_date_string returns [original, start, end]
    _, start, end = res
    assert (start, end) == (exp_start, exp_end)
