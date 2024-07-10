from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SelectField


class BathroomPassesForm(FlaskForm):
    teacher = SelectField()


class TeacherSelectForm(FlaskForm):
    teacher = SelectField()