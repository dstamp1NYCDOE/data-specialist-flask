def convert_days_to_cycle(days):
    days = str(days)
    conversion_list = [
        ("1", "M"),
        ("2", "T"),
        ("3", "W"),
        ("4", "Th"),
        ("5", "F"),
        ("5", "Sa"),
        ("-6", "-T-Th"),
    ]

    for cycle, day in conversion_list:
        days = days.replace(cycle, day)

    return days
