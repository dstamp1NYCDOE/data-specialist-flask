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


class caassSchoolMessengerAttendanceUpload(FlaskForm):
    date_of_interest = DateField(default=dt.datetime.today)
    CAASS_file = FileField(
        "Download Reports->Custom Reports->School Messenger Attendance",
        validators=[FileRequired()],
    )