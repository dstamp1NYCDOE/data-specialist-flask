from flask_wtf import FlaskForm

from wtforms import URLField

class UpdateClassListsOnGoogle(FlaskForm):
    gsheet_url = URLField("Google Sheet URL")
    
