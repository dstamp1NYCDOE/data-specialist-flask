from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileRequired
from wtforms import DateField


import datetime as dt


class SmartPassDataUploadForm(FlaskForm):
    date_of_interest = DateField(default=dt.datetime.today)
    smartpass_file = FileField(
        "Download the SmartPass Pass File as .CSV",
        validators=[FileRequired()],
    )
