from datetime import date, timedelta


def test_formula_expected_daily_hours() -> None:
    required_hours = 10
    completed_hours = 4
    today = date(2026, 6, 1)
    deadline = today + timedelta(days=2)

    remaining_hours = required_hours - completed_hours
    remaining_days = (deadline - today).days + 1

    assert remaining_hours / remaining_days == 2
