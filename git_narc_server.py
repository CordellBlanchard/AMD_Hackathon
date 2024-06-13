from flask import Flask, jsonify, request  
from flask_sqlalchemy import SQLAlchemy  
from utils.sarif_parser import parse_sarif_file, update_old_state  
from utils.blame_api import Repo, getLineInfo  
from apscheduler.schedulers.background import BackgroundScheduler  
  
app = Flask(__name__)  
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/dbname'  
db = SQLAlchemy(app)  
  
class SarifData(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    data = db.Column(db.JSON)  
    sarif_file = db.Column(db.String)  

    def serialize(self):
        return {
            'id': self.id,
            'data': self.data,
            'sarif_file': self.sarif_file
        } 
  
def check_for_new_sarif_file():  
    latest_sarif_data = SarifData.query.order_by(SarifData.id.desc()).first()  
    if latest_sarif_data.sarif_file != check_for_new_sarif_file.latest_sarif_file:  
        check_for_new_sarif_file.latest_sarif_file = latest_sarif_data.sarif_file  
        merge_sarif(latest_sarif_data.sarif_file)  
  
check_for_new_sarif_file.latest_sarif_file = None  
  
def merge_sarif(sarif_file_name):  
    new_dict = parse_sarif_file(sarif_file_name)  
    new_dict['blame'] = []
    new_dict['line_content'] = []
    # add blame info to new sarif file  
    for key in new_dict:  
        commit_hash = new_dict[key]['commit']  
        for file, line_number in zip(new_dict[key]['files'], new_dict[key]['lines']):  
            blame_info, line_content = getLineInfo(repo, commit_hash, file, line_number)  
            new_dict['blame'].append(blame_info)  
            new_dict["line_content"].append(line_content)  
  
    # get baseline_dict from database  
    baseline_dict = SarifData.query.order_by(SarifData.id.desc()).offset(1).first().data 
    if baseline_dict is None:
        # This is the first entry in the database, so there is no baseline
        baseline_dict = {}
    else:
        baseline_dict = baseline_dict.data
  
    # compare to baseline dict and update dictionary  
    latest_dict = update_old_state(new_dict, baseline_dict)  
  
    repo = Repo("tensorflow", "tensorflow") # this can also come from the something else (owner, repo_name)  
  
    # send the updated dictionary to the database  
    new_data = SarifData(data=latest_dict)  
    db.session.add(new_data)  
    db.session.commit()  
  
scheduler = BackgroundScheduler()  
scheduler.add_job(check_for_new_sarif_file, 'interval', seconds=3600) # checks for new sarif file every hour  
scheduler.start() 

@app.route('/sarifdata', methods=['GET'])
def get_sarif_data():
    all_data = SarifData.query.all()
    return jsonify([data.serialize() for data in all_data])
  
if __name__ == '__main__':  
    # run the flask server  
    app.run(debug=True)  
