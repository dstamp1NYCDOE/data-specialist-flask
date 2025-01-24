from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileRequired
from wtforms import DateField


import datetime as dt


class ScreenerUploadForm(FlaskForm):
    
    file = FileField(
        "Upload the Universal Screener File as .xlsx",
        validators=[FileRequired()],
    )
