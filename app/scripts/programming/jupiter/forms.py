from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import DateField, SelectField, StringField, IntegerField
from wtforms.validators import DataRequired, Regexp, InputRequired
from wtforms.widgets import NumberInput


from werkzeug.utils import secure_filename

import datetime as dt


class JupiterMasterScheduleForm(FlaskForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)