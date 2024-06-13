from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Issue
from datetime import datetime

main_bp = Blueprint('main', __name__)

# IMPORTANT : leave the root route to the Elastic Beanstalk Load Balancer health check, it performs a GET to '/' every 5 seconds and expects a '200'
@main_bp.route('/issue', methods=['GET'])
def list_issues():
    return 'Hi!?', 200

@main_bp.route('/register', methods=['POST'])
def register_user():
    try:
        
        data = request.get_json()
        print('\n\nData\n\n',data,'\n\n')
        new_user = User(
            email = data["email"],
            age = data["age"],
            timestamp = datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()
        return 'User added', 200
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500


@main_bp.route('/issues', methods=['GET'])
# implement optional filtering by author, severity, and file path
def c():
    try:
        author = request.args.get('author')
        severity = request.args.get('severity')
        file_path = request.args.get('file_path')
        query = db.session.query(Issue)
        if author:
            query = query.filter(Issue.author == author)
        if severity:
            query = query.filter(Issue.severity == severity)
        if file_path:
            query = query.filter(Issue.file_path == file_path)
        issues = query.all()
        return jsonify([i.serialize() for i in issues])
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500
    
#similar to list_issues(), implement an endpoint for list_blames()
@main_bp.route('/blames', methods=['GET'])
def list_blames():
    try:
        blames = db.session.query(Issue.author).distinct().all()
        return jsonify([b[0] for b in blames])
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500
