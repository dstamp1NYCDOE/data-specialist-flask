from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileRequired
from wtforms import DateField


import datetime as dt


class JupiterLoginUploadForm(FlaskForm):

    jupiter_login_file = FileField(
        "Download the Jupiter Login File as .CSV",
        validators=[FileRequired()],
    )
