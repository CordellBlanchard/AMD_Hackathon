from flask import Flask
from app import create_app, db
from apscheduler.schedulers.background import BackgroundScheduler
# the models need to be imported before calling db.create_all()
from app.models.models import SarifFile
from util.merge_issue_blame import merge_sarif

application = create_app()

with application.app_context():
    db.create_all()

latest_sarif_file = None

def check_for_new_sarif_file():  
    global latest_sarif_file
    latest_sarif_data = SarifFile.query.order_by(SarifFile.id.desc()).first()  
    if latest_sarif_data.sarif_file != latest_sarif_file:  
        latest_sarif_file = latest_sarif_data.sarif_file  
        merge_sarif(latest_sarif_data.sarif_file)

scheduler = BackgroundScheduler()  
scheduler.add_job(check_for_new_sarif_file, 'interval', seconds=10) # checks for new sarif file every hour  
scheduler.start() 

if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0")