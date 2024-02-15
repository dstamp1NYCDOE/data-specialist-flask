from flask import Flask, request, redirect, url_for, render_template
from forms import FileForm
from werkzeug.utils import secure_filename

import os 
import utils

app = Flask(__name__)

app.debug = True
app.secret_key = 'banana'

files_df = utils.return_dataframe_of_files()

@app.route('/')
def return_index():
    return 'Hello World'

@app.route('/view/<report>')
def view_most_recent_report(report):
    report_path = utils.return_most_recent_report(files_df, report)
    report_df = utils.return_file_as_df(report_path)
    report_html = report_df.to_html(classes=["table", "table-sm"])
    return render_template("viewReport.html", report_html=report_html)

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    form = FileForm()

    if form.validate_on_submit():
        f = form.file.data
        filename = secure_filename(f.filename)
        filename = filename.replace('_',"-")
        download_date = form.download_date.data
        year_and_semester = form.year_and_semester.data
        filename = f"{year_and_semester}_{download_date}_{filename}"
        f.save(os.path.join(app.root_path, "data", filename))
        return redirect(url_for("return_index"))

    return render_template("upload.html", form=form)
