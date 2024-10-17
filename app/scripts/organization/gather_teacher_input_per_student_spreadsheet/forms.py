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

from werkzeug.utils import secure_filename


class TeacherInputPerStudentSpreadsheetForm(FlaskForm):
    input_cols = StringField("Input Columns", widget=TextArea())
    data_validation_values = StringField("Data Validation Values - Put the default value first", widget=TextArea())
    spreadsheet_title = StringField("Subgroup title")

    teacher = SelectField(
        "Teacher",
        choices=[
            ("BOTH", "BOTH"),
            ("Teacher1", "Teacher1"),
            ("Teacher2", "Teacher2"),
            ("NoTeacherPages", "Counselors Only"),
        ],
        validators=[InputRequired()],
    )

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

    course_lst = StringField("Course List - Leave blank to include all courses", widget=TextArea())

    computer_labs_flag = BooleanField("Computer Labs Only", default=False)

    include_counselors_flag = BooleanField("Include Counselors", default=True)

    include_student_duplicates_flag = BooleanField("Include Student Duplicates by Teacher", default=True)
