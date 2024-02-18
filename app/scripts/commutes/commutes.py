from flask import render_template

import app.scripts.utils as utils
from app.scripts import scripts, files_df

@scripts.route("/commutes")
def return_commute_reports():
    return render_template("commutes/templates/commutes/index.html")