from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Regexp

from app.main.forms import school_year_and_semester_choices

class JupiterCourseSelectForm(FlaskForm):
    course_and_section = SelectField(
        "Which course/section to run report for?",
        choices=[],
    )


class TeacherJupiterAttdCompletionForm(FlaskForm):
    year_and_semester = SelectField(
        "School Year and Semester", choices=school_year_and_semester_choices,
    )    