from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileRequired
from wtforms import DateField


import datetime as dt


class PhoneCallsUploadForm(FlaskForm):

    file = FileField(
        "Upload the Phone Call Tracker File as .xlsx",
        validators=[FileRequired()],
    )
