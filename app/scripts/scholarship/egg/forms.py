from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField
from wtforms.validators import DataRequired, Regexp, InputRequired

import datetime as dt


class EggUploadForm(FlaskForm):
    
    egg_file = FileField(
        "Download EGG file from STARS Client for desired marking period",
        validators=[FileRequired()],
    )

    semester = SelectField(
        "Select Semester",
        choices=[('S1', "Semester 1"),('S2', "Semester 2")],
        validators=[InputRequired()],
    )