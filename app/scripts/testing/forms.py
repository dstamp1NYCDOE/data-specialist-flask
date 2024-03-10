from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Regexp, InputRequired

from werkzeug.utils import secure_filename


class CollegeBoardExamInvitationLetter(FlaskForm):
    student_testing_assignments = FileField(
        "Student Testing Assignments (preprocessed with StudentID)",
        validators=[FileRequired()],
    )

    exam_title = SelectField(
        "Select Exam",
        choices=[("SAT", "SAT"), ("PSAT", "PSAT")],
        validators=[InputRequired()],
    )

    exam_date = DateField()
