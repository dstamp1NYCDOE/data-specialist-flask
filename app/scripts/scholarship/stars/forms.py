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


class StaffMemberDropDown(FlaskForm):
    staff_member = SelectField(
        "Staff Member",
        choices=[],
        validators=[InputRequired()],
    )
