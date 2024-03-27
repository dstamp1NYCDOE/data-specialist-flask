from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import DateField, SelectField, StringField, IntegerField
from wtforms.validators import DataRequired, Regexp, InputRequired
from wtforms.widgets import NumberInput


from werkzeug.utils import secure_filename


class AttendanceBenchmarkForm(FlaskForm):

    in_class_percentage = IntegerField(
        "Present Percentage",
        widget=NumberInput(min=0, max=100, step=5),
        default=90,
    )

    on_time_percentage = IntegerField(
        "On Time Percentage",
        widget=NumberInput(min=0, max=100, step=5),
        default=80,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class StudentPrivilegeSummaryForm(AttendanceBenchmarkForm):

    StudentID = SelectField(
        "Select Student",
        choices=[(0, "Select Student")],
        validators=[InputRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
