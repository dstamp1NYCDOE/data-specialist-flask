from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField

from werkzeug.utils import secure_filename


class FileForm(FlaskForm):
    file = FileField(validators=[FileRequired()])
    download_date = DateField()
    year_and_semester = SelectField(
        "School Year and Semester",
        choices=[
            ("2023-2", "Spring 2024"),
            ("2023-1", "Fall 2023"),
            ("2022-7", "Summer 2023"),
            ("2022-2", "Spring 2023"),
            ("2022-1", "Fall 2022"),
            ("2021-7", "Summer 2022"),
            ("2021-2", "Spring 2022"),
            ("2021-1", "Fall 2021"),
        ],
    )
