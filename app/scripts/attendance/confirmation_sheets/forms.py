from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, MultipleFileField


import datetime as dt


class ConfirmationSheetsCoverPageForm(FlaskForm):
    
    jupiter_attendance_file = FileField('Download Jupiter Attendance File for the week of interest', validators=[FileRequired()])
    rdsc_files = MultipleFileField(
        "Attach all of the RDSC files for the week (save as .xlsx files from .XLS)",
        validators=[FileRequired()],
        render_kw={'multiple': True},
    )