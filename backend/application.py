import os
from flask import Flask
from app import create_app, db
from apscheduler.schedulers.background import BackgroundScheduler
# the models need to be imported before calling db.create_all()
from app.models.models import SarifFile, Issue, Blame
from app.util.merge_issue_blame import merge_sarif
from app.util.sarif_parser import scan_for_sarif

from tqdm import tqdm
from datetime import datetime

application = create_app()

def check_for_new_sarif_file(): 
    print("WE ARE RUNNING") 
    latest_sarif_data = SarifFile.query.order_by(SarifFile.date.desc()).first()
    dir_path = './app/database'
    all_files = scan_for_sarif(dir_path)  
    for file in tqdm(all_files):
        file_date = datetime.strptime(file[0], "%Y-%m-%d")
        file_path = file[1]
        if latest_sarif_data is None or file_date > latest_sarif_data.date:
            merge_sarif(os.path.join(dir_path, file_path))
            new_sarif = SarifFile(sarif_file=file_path, date=file_date)
            db.session.add(new_sarif)
            db.session.commit()

with application.app_context():
    db.create_all()
    check_for_new_sarif_file()

scheduler = BackgroundScheduler()  
scheduler.add_job(check_for_new_sarif_file, 'interval', minutes=60) # checks for new sarif file every hour  
scheduler.start() 

if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0")