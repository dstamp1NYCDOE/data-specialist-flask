from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired


class RegentsOrderingForm(FlaskForm):
    combined_regents_registration_spreadsheet = FileField(
        "Upload XLSX file of regents registrations",
        validators=[FileRequired()],
    )


class IdentifyExamOnlyForm(FlaskForm):
    combined_regents_registration_spreadsheet = FileField(
        "Upload XLSX file of regents registrations",
        validators=[FileRequired()],
    )


class ProcessRegentsPreregistrationSpreadsheetForm(FlaskForm):
    combined_regents_registration_spreadsheet = FileField(
        "Upload XLSX file of regents registrations",
        validators=[FileRequired()],
    )
