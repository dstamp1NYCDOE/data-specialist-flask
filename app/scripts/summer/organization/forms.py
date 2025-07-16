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


class SmartPassKioskLabels(FlaskForm):
    kiosk_file = FileField(
        "Upload SmartPass Kiosk File as .csv (Include columns username & password)",
        validators=[FileRequired()],
    )



class OrganizeStudentRecordsForm(FlaskForm):
    student_records_pdf = FileField(
        "Student Records as PDF",
        validators=[FileRequired()],
    )

    distribution_mode = SelectField(
        "Distribution Mode",
        choices=[("first_period","First Period of the Day"), ("last_period","Last Period of the Day")],
        validators=[InputRequired()],
    )

    student_records_pdf_orientation = SelectField(
        "Student Records PDF Page Orientation",
        choices=[("landscape", "Landscape"), ("portrait", "Portrait")],
        validators=[InputRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    