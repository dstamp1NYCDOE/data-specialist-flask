import os
import datetime as dt

from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField

import app.scripts.utils as utils


def _build_upload_form(report_codes):
    attrs = {
        f"file_{code}": FileField(code, validators=[FileRequired()])
        for code in report_codes
    }
    attrs["submit"] = SubmitField("Upload and Continue")
    return type("RequiredFilesUploadForm", (FlaskForm,), attrs)


class RequiredFilesForm:
    """
    Initialize with the report codes a service needs (e.g. ["1_08", "3_07"])
    and the current year_and_semester. Only renders an upload field for the
    reports actually missing on disk, and saves submitted files using the
    standard data/{year_and_semester}/{report}/ naming convention so the
    service can find them on retry.
    """

    def __init__(self, report_codes, year_and_semester):
        self.year_and_semester = year_and_semester
        self.missing_codes = [
            code
            for code in report_codes
            if not utils.report_exists(code, year_and_semester)
        ]
        # No explicit formdata: FlaskForm's default auto-combines
        # request.form and request.files, which FileField needs.
        self.form = _build_upload_form(self.missing_codes)()

    @property
    def is_satisfied(self):
        return not self.missing_codes

    def validate_on_submit(self):
        return self.form.validate_on_submit()

    def save(self):
        today = dt.date.today().isoformat()
        saved_filenames = []
        for code in self.missing_codes:
            file_storage = getattr(self.form, f"file_{code}").data
            report_name = code.replace("_", "-")
            extension = file_storage.filename.rsplit(".", 1)[-1]
            filename = f"{self.year_and_semester}_{today}_{report_name}.{extension}"
            path = os.path.join(
                current_app.root_path, f"data/{self.year_and_semester}/{report_name}"
            )
            os.makedirs(path, exist_ok=True)
            file_storage.save(os.path.join(path, filename))
            saved_filenames.append(filename)
        return saved_filenames
