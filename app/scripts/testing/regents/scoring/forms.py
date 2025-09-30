from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import DateField, SelectField, BooleanField
from wtforms.validators import DataRequired, Regexp, InputRequired


class UploadREDS(FlaskForm):
    reds_xlsx = FileField(
        "Upload XLSX file of REDS File",
        validators=[FileRequired()],
    )


    check_INC = BooleanField("Check for INC", default=False)


    parts_to_check = SelectField(
        "Parts to Check",
        choices=[
            ("Part1Part2", "BOTH"),
            ("Part1", "Part1"),
            ("Part2", "Part2"),
        ],
        validators=[InputRequired()],
    )