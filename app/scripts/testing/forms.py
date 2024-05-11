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


class CollegeBoardExamTicketsLetter(FlaskForm):
    exam_date = DateField()

    student_exam_tickets = FileField(
        "Student Exam Tickets as PDF",
        validators=[FileRequired()],
    )

    student_testing_assignments = FileField(
        "Student Testing Assignments (preprocessed with StudentID)",
        validators=[FileRequired()],
    )


class ProcessWalkingSpreadsheet(FlaskForm):
    walkin_spreadsheet_file = FileField(
        "WalkIn Signup Spreadsheet",
        validators=[FileRequired()],
        description="File must be saved as .xlsx",
    )
