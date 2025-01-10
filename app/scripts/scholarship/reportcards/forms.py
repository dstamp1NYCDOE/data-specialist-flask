from flask import session
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


class EnhancedReportCardForm(FlaskForm):
    marking_period = SelectField(
        "Marking Period",
        choices=[
            ("1", "MP1"),
            ("2", "MP2"),
            ("3", "MP3"),
        ],
        validators=[InputRequired()],
    )