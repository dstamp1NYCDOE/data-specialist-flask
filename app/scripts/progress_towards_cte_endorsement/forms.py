from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SelectField

from app.main.forms import MARKING_PERIOD_CHOICES


class PlaceholderForm(FlaskForm):
    marking_period = SelectField(
        "Marking Period", choices=MARKING_PERIOD_CHOICES,
    )
    cr_1_14 = FileField("CR 1.14 - Transcript (optional, uses most recent upload if left blank)")
    cr_1_30 = FileField("CR 1.30 - Mark Conversion (optional)")
    cr_3_07 = FileField("CR 3.07 - Cohort/GEC (optional)")
    cr_1_49 = FileField("CR 1.49 - Counselor (optional)")
