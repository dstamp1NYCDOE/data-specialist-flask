from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileRequired

class SurveyUploadForm(FlaskForm):

    file = FileField(
        "Upload the Survey File as .CSV",
        validators=[FileRequired()],
    )
