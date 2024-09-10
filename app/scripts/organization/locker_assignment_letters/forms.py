from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import DateField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Regexp, InputRequired


class LockerAssignmentFileUploadForm(FlaskForm):
    locker_assignment_csv = FileField(
        "Upload CSV file of locker assignments",
        validators=[FileRequired()],
    )