

from flask import render_template, request, send_file, session


from app.scripts import scripts

    
from app.scripts.family_engagement.jupiter_logins_analysis.forms import JupiterLoginUploadForm
from app.scripts.family_engagement.jupiter_logins_analysis.main import return_jupiter_logins_analysis
@scripts.route("/family_engagement/jupiter_logins_analysis", methods=['GET','POST'])
def return_family_engagement_jupiter_logins_analysis():
    if request.method == 'GET':
        form = JupiterLoginUploadForm()
        return render_template('family_engagement/jupiter_logins_analysis/templates/form.html', form=form)
    else:
        form = JupiterLoginUploadForm(request.form)

        f, download_name = return_jupiter_logins_analysis(form, request)
        
        mimetype = "application/pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype,
        )    