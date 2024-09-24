import datetime as dt

marking_period_dates = {
    2023:[
        ('S2-MP3',dt.datetime(2024, 5, 1)),
        ('S2-MP2',dt.datetime(2024, 3, 14)),
        ('S2-MP1',dt.datetime(2024, 1, 30)),
        ('S1-MP3',dt.datetime(2023, 12, 4)),
        ('S1-MP2',dt.datetime(2023, 10, 19)),
        ('S1-MP1',dt.datetime(2023, 9, 7)),
    ],
    2024:[
        ('S2-MP3',dt.datetime(2025, 5, 5)),
        ('S2-MP2',dt.datetime(2025, 3, 17)),
        ('S2-MP1',dt.datetime(2025, 1, 28)),
        ('S1-MP3',dt.datetime(2024, 12, 2)),
        ('S1-MP2',dt.datetime(2024, 10, 16)),
        ('S1-MP1',dt.datetime(2024, 9, 6)),
    ]
}

def return_mp_from_date(date, school_year):
    mp_date_tuples = marking_period_dates[school_year]
    for mp, mp_start_date in mp_date_tuples:
        if date >= mp_start_date:
            return mp
