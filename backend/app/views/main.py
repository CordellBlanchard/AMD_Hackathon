from flask import Blueprint, request, jsonify
from app import db
#from app.models.models import User
from app.models.models import Issue, Rule
from datetime import datetime

main_bp = Blueprint('main', __name__)

# IMPORTANT : leave the root route to the Elastic Beanstalk Load Balancer health check, it performs a GET to '/' every 5 seconds and expects a '200'
@main_bp.route('/', methods=['GET'])
def EB_healthcheck():
    return 'OK', 200

# @main_bp.route('/register', methods=['POST'])
# def register_user():
#     try:
        
#         data = request.get_json()
#         print('\n\nData\n\n',data,'\n\n')
#         new_user = User(
#             email = data["email"],
#             age = data["age"],
#             timestamp = datetime.utcnow()
#         )
#         db.session.add(new_user)
#         db.session.commit()
#         return 'User added', 200
#     except Exception as e:
#         db.session.rollback()
#         return f'An error occurred: {str(e)}', 500


@main_bp.route('/list', methods=['GET'])
def list_users():
    try:
        issues = db.session.query(Issue).all()
        # calling the __str__ representation defined in the User model 
        return jsonify([i.serialize() for i in issues])
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500
    
   
# Create endpoint to retrieve rule information
@main_bp.route('/rules', methods=['GET'])
def list_rules():
    try:
        rules = db.session.query(Rule).all()
        return jsonify([r.serialize() for r in rules])
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500    
    
# Query the database for a specific rule 
@main_bp.route('/rule/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    try:
        rule = db.session.query(Rule).filter_by(id=rule_id).all()
        return jsonify(rule.serialize())
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500