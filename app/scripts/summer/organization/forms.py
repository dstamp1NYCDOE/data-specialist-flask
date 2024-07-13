from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField, IntegerField
from wtforms.validators import DataRequired, Regexp, InputRequired
from wtforms.widgets import NumberInput


class BathroomPassesForm(FlaskForm):
    teacher = SelectField()


class TeacherSelectForm(FlaskForm):
    teacher = SelectField()


class ZippedPhotosForm(FlaskForm):
    mapping_file = FileField(
        "Upload SmartPass Mapping File",
        validators=[FileRequired()],
    )

    batch_size = IntegerField(
        "Number of Photos in Zip File",
        widget=NumberInput(min=0, max=500, step=25),
        default=400,
    )

    batch_number = IntegerField(
        "Batch Number",
        widget=NumberInput(min=1, max=10, step=1),
        default=1,
    )
