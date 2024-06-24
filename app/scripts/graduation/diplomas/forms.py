from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired


class DiplomaMockupForm(FlaskForm):
    grad_list_file = FileField(
        "Upload .csv file of Graduation Certification Spreadsheet",
        validators=[FileRequired()],
    )
