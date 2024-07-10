from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileRequired
from wtforms import DateField


import datetime as dt

class RDALUploadForm(FlaskForm):
    class_date = DateField(
        default=dt.datetime.today
    )
    rdal_file = FileField(
        "Save the RDAL file as a .CSV before uploading",
        validators=[FileRequired()],
    )
