from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Regexp


class CommuteByClassForm(FlaskForm):
    course_and_section = SelectField(
        "Which course and section to run report form?",
        choices=[],
    )
