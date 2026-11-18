from datetime import date

import pytest
from scripts.sprint import date_ranges, render_sql


def test_sql_batch_ranges_cover_dates_without_overlap():
    periods = date_ranges(date(2020, 11, 1), date(2020, 11, 21), 7)
    assert len(periods) == 3
    assert periods[0] == (date(2020, 11, 1), date(2020, 11, 7))
    assert periods[1] == (date(2020, 11, 8), date(2020, 11, 14))
    assert periods[2] == (date(2020, 11, 15), date(2020, 11, 21))


def test_generated_sql_replaces_both_dates():
    sql = render_sql(date(2020, 12, 1), date(2020, 12, 4))
    assert "_TABLE_SUFFIX BETWEEN '20201201' AND '20201204'" in sql
    assert "_TABLE_SUFFIX BETWEEN '20201101' AND '20201107'" not in sql


def test_date_range_rejects_invalid_and_out_of_window():
    with pytest.raises(ValueError):
        date_ranges(date(2020, 10, 1), date(2020, 11, 2), 7)
    with pytest.raises(ValueError):
        date_ranges(date(2020, 11, 10), date(2020, 11, 1), 7)
    with pytest.raises(ValueError):
        date_ranges(date(2020, 11, 1), date(2020, 11, 7), 0)
