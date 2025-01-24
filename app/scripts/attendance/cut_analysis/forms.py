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