from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import DateField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Regexp, InputRequired

exam_title_choices = [
    ("ALL", "ALL"),
    ("ELA", "ELA"),
    ("Global", "Global History"),
    ("USH", "US History"),
    ("Alg1", "Algebra I"),
    ("Geo", "Geometry"),
    ("Alg2", "Algebra II/Trigonometry"),
    ("LE", "Living Environment"),
    ("ES", "Earth Science"),
    ("Chem", "Chemistry"),
    ("Phys", "Physics"),
]


class RegentsOrganizationExamSelectForm(FlaskForm):
    exam_title = SelectField(
        "Select Exam",
        choices=exam_title_choices,
        validators=[InputRequired()],
    )


import datetime as dt


class EarthSciencePracticalForm(FlaskForm):
    practical_date = DateField(default=dt.datetime.today)
    practical_times = TextAreaField()
    exam_title = TextAreaField()
