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

class EnhancedLineScheduleForm(FlaskForm):
    subset_lst = StringField("StudentID List", widget=TextArea())
    subset_title = StringField("Subgroup title")

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