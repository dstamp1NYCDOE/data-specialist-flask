from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (
    DateField,
    SelectField,
    StringField,
    SelectMultipleField,
    BooleanField,
)
from wtforms.validators import DataRequired, Regexp, InputRequired
from wtforms.widgets import TextArea

from werkzeug.utils import secure_filename


class PrepareFinalTranscriptWithDischargeDateForm(FlaskForm):
    transcript_file = FileField(
        "Student Transcripts as PDF",
        validators=[FileRequired()],
    )

    discharge_date = DateField()