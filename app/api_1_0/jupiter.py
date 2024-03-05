from flask import jsonify, request, session

import app.scripts.utils as utils
from app.api_1_0 import api, files_df

@api.route("/jupiter/classes")
def return_jupiter_classes():
    report = "rosters_and_grades"
    filename = utils.return_most_recent_report(files_df, report)

    df = utils.return_file_as_df(filename).fillna('')
    term = session['term']
    df = df[df['Term']==f'S{term}']
    df = df.drop_duplicates(subset=['Course','Section'], keep='last')
    df = df.sort_values(by=['Teacher1','Course','Section'])
    return jsonify(df.to_dict(orient='records'))
