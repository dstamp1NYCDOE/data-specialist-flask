from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Regexp, InputRequired

from werkzeug.utils import secure_filename


class IPRMonitoringForm(FlaskForm):
    cr_1_73 = FileField(
        "Upload STARS CR 1.73",
        validators=[FileRequired()],
    )
