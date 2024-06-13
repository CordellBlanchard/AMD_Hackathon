from flask import Blueprint, request, jsonify
from sqlalchemy import or_, func

from app import db
#from app.models.models import User
from app.models.models import Issue, Blame, issue_blame, LLMCache
from datetime import datetime 
from collections import defaultdict
from app.util.llm import get_llm_response, create_cache 

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
    

@main_bp.route('/group_issues', methods=['GET'])
def group_issues():
    try:
        # Get query parameters
        group_by = request.args.get('group_by')

        # Start with all Issues
        query = db.session.query(Issue, Blame).select_from(Issue).join(issue_blame).join(Blame)

        if group_by:
            if group_by == 'id':
                # Group by issue id
                query = query.order_by(Issue.id)
            elif group_by == 'rule':
                # Group by rule id
                query = query.order_by(Issue.rule)
            elif group_by in ['file', 'author_name']:
                # Group by blame file or author name
                query = query.order_by(getattr(Blame, group_by))
        
        # Execute the query
        issue_blame_pairs = query.all()

        # Group the results
        grouped_issues = defaultdict(list)
        for issue, blame in issue_blame_pairs:
            key = getattr(issue if group_by in ['id', 'rule'] else blame, group_by)
            grouped_issues[key].append(issue.serialize())

        return jsonify(grouped_issues)
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500

@main_bp.route('/list', methods=['GET'])
def list_users():
    try:
        issues = db.session.query(Issue).all()
        # calling the __str__ representation defined in the User model 
        return jsonify([i.serialize() for i in issues])
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500
    
@main_bp.route('/llm_cache', methods=['GET'])
def view_cache():
    try:
        cache = db.session.query(LLMCache).all()
        # calling the __str__ representation defined in the User model 
        return jsonify([i.serialize() for i in cache])
    
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500

@main_bp.route('/generate_llm_response', methods=['POST'])
def generate_llm_response():
    data = request.get_json()

    # Extract required parameters from the request
    rule_info = data.get("rule_info")
    issue_message = data.get("issue_message")
    file = data.get("file")
    line = data.get("line")
    commit_hash = data.get("commit_hash")
    blame_id = data.get("blame_id")

    # Check if all required parameters are provided
    if not all([rule_info, issue_message, file, line, commit_hash, blame_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Use the helper function
    result, status_code = handle_llm_response(rule_info, issue_message, file, line, commit_hash, blame_id)
    return jsonify(result), status_code


def handle_llm_response(rule_info, issue_message, file, line, commit_hash, blame_id):
    try:
        # Generate the LLM response
        response = get_llm_response(rule_info, issue_message, file, line, commit_hash)

        # Create cache entry
        create_cache(blame_id, response)

        return {"message": "LLM response generated and cached successfully", "response": response}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": f'An error occurred: {str(e)}'}, 500


@main_bp.route('/test_llm', methods=['GET'])
def test_llm():
    try:
        id = 5 
        # Retrieve the specific issue by ID
        issue = Issue.query.get(id)
        if not issue:
            return jsonify({"error": "Issue not found"}), 404

        # Serialize the issue data
        issue_data = issue.serialize()

        # Access the first blame associated with the issue
        first_blame = issue.blames[0] if issue.blames else None
        commit_hash = issue.commit 
        issue_message =  issue.description
        blame_id = issue.blames[0].id
        file = issue.blames[0].file
        line =  issue.blames[0].starting_line
        rule_info = issue.rule.fullDescription

        # Use the helper function
        result, status_code = handle_llm_response(rule_info, issue_message, file, line, commit_hash, blame_id)
        return jsonify(result), status_code

    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500
    
