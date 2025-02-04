from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (
    DateField,
    SelectField,
    StringField,
    SelectMultipleField,
    BooleanField,
)
from wtforms.validators import DataRequired, Regexp, InputRequired
from wtforms.widgets import TextArea

import datetime as dt
from app.scripts import scripts, files_df
import app.scripts.utils as utils
import pandas as pd

from flask import session

class ProspectiveCuttingFromCAASSForm(FlaskForm):
    date_of_interest = DateField(default=dt.datetime.today)
    CAASS_file = FileField(
        "Download Reports->Custom Reports->School Messenger Attendance",
        validators=[FileRequired()],
    )

    periods = SelectMultipleField(
        "Periods",
        choices=[
            ("ALL", "ALL"),
            ("1", "P1"),
            ("2", "P2"),
            ("3", "P3"),
            ("4", "P4"),
            ("5", "P5"),
            ("6", "P6"),
            ("7", "P7"),
            ("8", "P8"),
            ("9", "P9"),
        ],
        validators=[InputRequired()],
        default=["ALL"],
    )

class AttendanceWeekOfForm(FlaskForm):
    week_of = SelectField(
        "Select Week Of",
        choices=[],
        validators=[InputRequired()],
    )

    def __init__(self, *args, **kwargs):
        super(AttendanceWeekOfForm, self).__init__(*args, **kwargs)

        school_year = session["school_year"]
        term = session["term"]
        year_and_semester = f"{school_year}-{term}"
        jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
        attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

        dates_df = attendance_marks_df[['Date']].drop_duplicates()
        dates_df['date'] = pd.to_datetime(dates_df['Date'])
        dates_df['week_number'] = dates_df['date'].dt.isocalendar().week
        dates_df = dates_df.drop_duplicates(subset=['week_number'])
        
        dates_df['label'] = dates_df['Date'].apply(lambda x:f'Week of {x}')
        df = dates_df[['week_number','label']]
        self.week_of.choices = list(zip(*df.values.T))

class AttendanceDayOfForm(FlaskForm):
    day_of = SelectField(
        "Select Date",
        choices=[],
        validators=[InputRequired()],
    )

    def __init__(self, *args, **kwargs):
        super(AttendanceDayOfForm, self).__init__(*args, **kwargs)

        school_year = session["school_year"]
        term = session["term"]
        year_and_semester = f"{school_year}-{term}"
        jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
        attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

        dates_df = attendance_marks_df[['Date']].drop_duplicates()

        df = dates_df[['Date','Date']]
        self.day_of.choices = list(zip(*df.values.T))            