from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Regexp

from app.main.forms import school_year_and_semester_choices, MARKING_PERIOD_CHOICES, COHORT_YEAR_CHOICES


class GenericForm(FlaskForm):
    pass

class CohortYearChoiceForm(FlaskForm):
    cohort_code = SelectField(
        "Cohort Year", choices=COHORT_YEAR_CHOICES,
    )  

class MarkingPeriodChoiceForm(FlaskForm):
    marking_period = SelectField(
        "Marking Period", choices=MARKING_PERIOD_CHOICES,
    )    