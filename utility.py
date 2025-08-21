from datetime import date, timedelta


def get_last_working_day()->date:
    """
    Calculates the last working day (Monday-Friday) from a today.
    """
    # Get the weekday of the current_date (Monday is 0, Sunday is 6)
    weekday = date.today().weekday()

    if weekday == 0:  # If it's Monday, the last working day was Friday
        days_to_subtract = 3
    elif weekday == 6:  # If it's Sunday, the last working day was Friday
        days_to_subtract = 2
    else:  # For Tuesday-Saturday, the last working day was the previous day
        days_to_subtract = 1

    last_working_day = date.today() - timedelta(days=days_to_subtract)
    return last_working_day