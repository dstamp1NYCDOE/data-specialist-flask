from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import DateField, SelectField, IntegerField
from wtforms.validators import DataRequired, Regexp, InputRequired


class MetroCardOrganizationFileUploadForm(FlaskForm):
    metrocard_student_organization_file = FileField(
        "Upload XLSX file of MetroCard organization file with StudentID, Teacher, and Room Number",
        validators=[FileRequired()],
    )

    starting_serial_number = IntegerField(
        "Starting Serial Number",
        validators=[InputRequired()]
    )