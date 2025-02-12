from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Regexp, InputRequired

from werkzeug.utils import secure_filename


class JupiterAttdUpload(FlaskForm):
    jupiter_attd_file = FileField(
        "Upload one day of Jupiter Attendance Export",
        validators=[FileRequired()],
    )
