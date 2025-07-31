from flask_wtf import FlaskForm

from wtforms import (
    DateField,
    SelectField,
    StringField,
    SelectMultipleField,
    BooleanField,
)
from wtforms.validators import DataRequired, Regexp, InputRequired
from wtforms.widgets import TextArea


class StudentIDForm(FlaskForm):
    students_str = StringField("StudentID List", widget=TextArea())