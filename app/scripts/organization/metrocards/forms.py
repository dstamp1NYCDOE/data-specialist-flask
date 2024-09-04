from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import DateField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Regexp, InputRequired


class MetroCardOrganizationFileUploadForm(FlaskForm):
    metrocard_student_organization_file = FileField(
        "Upload XLSX file of MetroCard organization file with StudentID, Teacher, and Room Number",
        validators=[FileRequired()],
    )

    metrocard_tbl = TextAreaField(default="StartingSerialNumber\t#_of_cards")
