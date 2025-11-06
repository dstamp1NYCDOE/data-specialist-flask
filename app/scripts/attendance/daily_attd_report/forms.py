from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileRequired
from wtforms import DateField


import datetime as dt


class DailyAttendanceReportForm(FlaskForm):
    daily_jupiter_attd_file = FileField(
        "Download Jupiter Attendance file as .csv",
        validators=[FileRequired()],
    )
